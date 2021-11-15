from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(inverse='_inverse_state')
    state_approv = fields.Selection(inverse='_inverse_state_approv')

    @api.multi
    def _inverse_state(self):
        if ((self.state_approv != 'to_approve_manager' and self.state == 'cancel') or
            (self.state_approv != 'to_approve_direktur' and self.state == 'cancel')):
            self.send_email('rejected')

    @api.multi
    def _inverse_state_approv(self):
        if self.state_approv == 'to_approve_direktur':
            self.send_email('approved_manager')

        if self.state_approv == 'approved':
            self.send_email('approved_direktur')

    @api.model
    def _cron_send_email(self):
        self.send_email_cron('to_approve_manager')
        self.send_email_cron('to_approve_direktur')

    def send_email(self, state):
        user = self.create_uid

        template_id = ''
        if state == 'rejected':
            template_id = self.env.ref('bms_approval_notification.po_user_notification_rejected_email_template').id
        if state == 'approved_manager':
            template_id = self.env.ref('bms_approval_notification.po_user_notification_approved_manager_email_template').id
        if state == 'approved_direktur':
            template_id = self.env.ref('bms_approval_notification.po_user_notification_approved_direktur_email_template').id
        
        print('template id:', template_id)
        template = self.env['mail.template'].browse(template_id)
        print('template: ', template)
        data = {'to': user.email}
        template.with_context(data).send_mail(self.id, force_send=True)

    def send_email_cron(self, state):
        query = """select distinct res_users_id as id
                    from bms_approval_notification_res_users_rel r
                    join bms_approval_notification a
                    on r.bms_approval_notification_id = a.id
                    where a.document_state = '""" + state + "'"

        self._cr.execute(query)

        users = self.env.cr.fetchall()

        for user in users:
            res_user = self.env['res.users'].search([('id', 'in', user)])

            approvals = self.env['bms.approval.notification'].search([
                ('document_state', '=', state),
                ('user_ids', 'in', [res_user.id])
            ])
                
            doc_types = []

            for approval in approvals:
                doc_types.append(approval.document_id.id)

            print(' user : ', res_user.name)
            print(' approval : ', doc_types)

            docs = self.search([('state', '=', 'draft'), ('state_approv', '=', state), ('doc_type_id', 'in', doc_types)])

            if docs:
                template_id = self.env.ref('bms_approval_notification.po_approver_notification_email_template').id
                template = self.env['mail.template'].browse(template_id)

                data = {'to': res_user.email, 'docs': docs}
                template.with_context(data).send_mail(self.id, force_send=True)