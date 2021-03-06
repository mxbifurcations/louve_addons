# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Private section
    @api.model
    @api.one
    # Later, we may want to implement other valid_psi options
    def _valid_psi(self, method):
        if method == 'first':
            return self._first_valid_psi()
        elif method == 'all':
            return self._all_valid_psi()
        else:
            return False

    @api.model
    @api.one
    def _all_valid_psi(self):
        today = fields.Date.today()
        if not self.product_tmpl_id.seller_ids:
            return False
        valid_si = self.product_tmpl_id.seller_ids.filtered(
            lambda si, t=today: ((not si.date_start or si.date_start <= t) and
                                 (not si.date_end or si.date_end >= t)))
        return valid_si

    @api.model
    @api.one
    def _first_valid_psi(self):
        if not self.product_tmpl_id.seller_ids:
            return False
        valid_si = self._all_valid_psi()[0]
        seq = min([si.sequence for si in valid_si])
        return valid_si.filtered(lambda si, seq=seq: si.sequence == seq)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Constraints section
    _sql_constraints = [
        (
            'psi_product_name_uniq', 'unique(name, product_id)',
            """You cannot register several times the same supplier on a"""
            """ product!"""),
    ]

    # Private section
    def _delete_duplicates(self, cr, uid, ids=None, context=None):
        query = """
            SELECT pp.id
            FROM
                product_supplierinfo psi
                INNER JOIN product_template pt ON psi.product_id = pt.id
                INNER JOIN product_product pp ON pp.product_tmpl_id = pt.id
            GROUP BY
                pp.id, psi.name
            HAVING
                count(*) > 1"""
        cr.execute(query)
        product_ids = map(lambda x: x[0], cr.fetchall())
        products = self.pool.get('product.product').browse(
            cr, uid, product_ids, context=context)

        deleted_ids = []
        for product in products:
            delete = False
            for psi in product.seller_ids:
                if delete:
                    deleted_ids.append(psi.id)
                    psi.unlink()
                else:
                    delete = True
        return deleted_ids
