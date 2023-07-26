import datetime
import json
import urllib3
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import requests

class OdooApiTesting(models.Model):
    _name = 'odoo.api.testing'
    _description = 'odoo_api_testing'
    _inherit="stock.picking"
    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()
    user_id = fields.Many2one('res.users', 'Current User', compute='_get_current_user')
    image = fields.Binary('odoo.api.testing')

    @api.model
    def _get_current_user(self):
      self.user_id = self.env.user.id

    def notify(self):
        check_state = self.env['stock.picking'].search([('partner_id','=',8)])
        states = []
        for state in check_state:
            states.append(state.state)
        if(check_state):
                raise ValidationError (states)
        else:
            pass
    
    def sendReq(self):
        check_state = self.env['stock.picking'].search([('origin','=',"S00007")])
        states = []
        for state in check_state:
            states = []
            states.append(state.state)
        if("done" in states):
                encoded_body = json.dumps({ "name": "done" })          
                http = urllib3.PoolManager()
                http.request("POST", "https://test-a5f09-default-rtdb.firebaseio.com/users.json", body=encoded_body, headers={"Content-Type":"application/json","auth":"ZA2AAsPGFTXUIG3IpYLRNXOkysISWMlTKJWQPH71"})
        if("assigned" in states):
                encoded_body = json.dumps({ "name": "assigned" })          
                http = urllib3.PoolManager()
                http.request("POST", "https://test-a5f09-default-rtdb.firebaseio.com/users.json", body=encoded_body, headers={"Content-Type":"application/json","auth":"ZA2AAsPGFTXUIG3IpYLRNXOkysISWMlTKJWQPH71"})
        if("waiting" in states):
                encoded_body = json.dumps({ "name": "done" })          
                http = urllib3.PoolManager()
                http.request("POST", "https://test-a5f09-default-rtdb.firebaseio.com/users.json", body=encoded_body, headers={"Content-Type":"application/json","auth":"ZA2AAsPGFTXUIG3IpYLRNXOkysISWMlTKJWQPH71"})
        else:
                pass

    def update_vip_state(self):
        partners = self.env['res.partner'].sudo().search([])
        subscribers = self.env['vip.subscribe'].sudo().search([])
        not_valid_ids = []
        valid_ids = []
        partners = []
        for s in subscribers:
                partners = self.env['res.users'].sudo().search([('partner_id.id','=',s.subscriber_id.id)])
                if s.end_date < datetime.date.today():
                        for p in partners:
                                not_valid_ids.append(p.id)
                                p.write({
                                    'is_vip':False
                                })
                else:
                        for p in partners:
                                valid_ids.append(p.id)
                                p.write({
                                        'is_vip':True
                                })
        http_request = None
        http_request = urllib3.PoolManager()
        encoded_body1 = json.dumps({"time":int(round(datetime.datetime.now().timestamp())),"title":"Vip Expiration","message":"You're subscription is expired please make sure to renew"})
        encoded_body2 = json.dumps({"time":int(round(datetime.datetime.now().timestamp())),"title":"Vip Subscription","message":"Congrats, you are now a VIP member with Quico Tech"})
        resp = requests.get("https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/VIP.json",headers={'Accept': 'application/json'})
        json_body = resp.json()
        ids = []
        for i in json_body:
                ids.append(int(i))
        for p in not_valid_ids:
                if p not in ids:
                        http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/VIP/"+str(p)+"/"+".json",body=encoded_body1,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                        print("yes")
                else:
                        for i in json_body:
                                if(int(i) == p):
                                        if (json_body[i]['title'] == "Vip Expiration"):
                                                pass
                                        else:
                                                http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/VIP/"+str(p)+"/"+".json",body=encoded_body1,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                                                print("yes")
        for p in valid_ids:
                if p not in ids:
                        http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/VIP/"+str(p)+"/"+".json",body=encoded_body2,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                        print ("yes")       
                else:
                        for j in json_body:
                                if(int(j) == p):
                                        if (json_body[j]['title'] == "Vip Subscription"):
                                                pass
                                        else:
                                                http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/VIP/"+str(p)+"/"+".json",body=encoded_body2,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})       
                                                print ("yes")
class VipSubscribe(models.Model):
        _name="vip.subscribe"
        
        subscriber_id = fields.Many2one("res.partner","Subscriber")
        cost = fields.Float(string="Cost")
        start_date = fields.Date(string="Start Date")
        end_date = fields.Date(compute="calculate_end_date",string="End Date",store=True)

        @api.depends('start_date')
        def calculate_end_date(self):
                mounth = ""
                for s in self:
                        if s.start_date:
                           date_st = fields.Date.from_string(s.start_date)
                           dt = date_st + relativedelta(months=3) 
                           mounth = fields.Date.to_string(dt) 
                        s.update({'end_date': mounth})

class Banners (models.Model):
        _name = "banners"

        image_1 = fields.Image(attachment=False)
        image_2 = fields.Image(attachment=False)
        image_3 = fields.Image(attachment=False)
        image_4 = fields.Image(attachment=False)
        image_5 = fields.Image(attachment=False)
        
class ProductTemplate(models.Model):
        _inherit = "product.template"

        vip = fields.Boolean(string="Is VIP")
        vip_price = fields.Float(string="VIP price")
        sale = fields.Boolean(string="Is on Sale")
        sale_percent = fields.Selection([('5',"5%"),('10',"10%"),('15',"15%"),('20',"20%"),
        ('25',"25%"),('30',"30%"),('35',"35%"),('40',"40%"),('45',"45%"),('50',"50%"),
        ("55","55%"),('60',"60%"),("65","65"),('70',"70%"),("75","70%"),('80',"80%"),
        ('90',"90%"),("95","95%")],"Discount %")
        sale_price = fields.Float(string="Discount Price", compute= "_calculate_price",readonly=False,store = True)
        hot_deal = fields.Boolean(string="Hot Deal",default=False)
        offer = fields.Boolean(string="Offers",default=False)
        product_priority = fields.Integer("Priority")

        @api.depends('sale_percent')
        def _calculate_price(self):
                cost = self.list_price
                discount  = (cost*float(self.sale_percent))/100
                self.sale_price = cost - discount
                return

class ProductTemplateAttributeValue(models.Model):
        _inherit = "product.attribute.value"

        image = fields.Binary(string="Image",attachment=False)

class ProductCategory(models.Model):
        _inherit='product.category'

        image = fields.Image('product.category',attachment=False)
        priority = fields.Integer("Priority")

class Cart(models.Model):
        _name = "cart"

        product_id = fields.Many2one("product.template")
        quantity = fields.Float("quantity")
        partner_id = fields.Many2one("res.partner")
        
class Wishlist(models.Model):
        _name = "wishlist"

        product_id = fields.Many2one("product.template")
        partner_id = fields.Many2one("res.partner")

class SaleOrder(models.Model):
        _inherit = "sale.order"

        payment_method = fields.Selection([('pay by cart',"Pay by Cart"),('cash on delivery',"Cash on Delivery")],"Payment Method",default="cash on delivery")
        service_order = fields.Boolean(string="is Service Order",default=False)
        review = fields.Text(string="Review")
        order_rate = fields.Float(string='Rating', digits=(1, 1), range='0,5')

class ResPartner (models.Model):
        _inherit = "res.partner"

        is_vip = fields.Boolean (default = False)
        show_add_button = fields.Boolean(default=False,store=False,compute="_change_add_button_state")
        show_renew_button = fields.Boolean(default=False,store=False,compute="_change_renew_button_state")
        dob = fields.Date ("DOB")
        
        def _change_add_button_state(self):
                subscribers = self.env['vip.subscribe'].sudo().search([('subscriber_id.id','=',self.id)])
                if subscribers:
                        self.show_add_button = False
                else:
                        self.show_add_button = True
        
        def _change_renew_button_state(self):
                subscribers = self.env['vip.subscribe'].sudo().search([('subscriber_id.id','=',self.id)])
                if subscribers and self.is_vip != True:
                        self.show_renew_button = True
                else:
                        self.show_renew_button = False
        
        def add_subscriber(self):
                self.env['vip.subscribe'].sudo().create({
                        "subscriber_id":self.id,
                        "cost":10,
                        "start_date":datetime.date.today()
                })
                self.write({
                        'is_vip':True
                })

        def renew_subscriber(self):
                subscribers = self.env['vip.subscribe'].sudo().search([('subscriber_id.id','=',self.id)])
                for s in subscribers:
                        s.write({
                                "end_time":s.end_time + relativedelta(months=+3)
                        })     
        
class ButtonConfirmSale(models.Model):
        _inherit = 'sale.order'

        def action_confirm(self):
                http_request = None
                http_request = urllib3.PoolManager()
                encoded_body = None
                user = None
                for order in self:
                        stock = self.env['stock.picking'].sudo().search([('origin','=',order.name)])
                        for s in stock:
                                s.write({
                                     'state':'waiting'   
                                })
                        partner = self.env['res.partner'].sudo().search([('parent_id.id','!=',False)])
                        partners = []
                        for i in partner:
                                partners.append(i.id)
                        if order.partner_id.id in partners:
                                current_id = order.partner_id.parent_id.id
                                user = self.env['res.users'].sudo().search([('partner_id.id','=',current_id)])
                        else:
                                user = self.env['res.users'].sudo().search([('partner_id.id','=',order.partner_id.id)])
                        encoded_body = json.dumps({"read":False,"time":int(round(datetime.datetime.now().timestamp())),"order_nb":order.name,"status":"Packaging","email":order.partner_id.email})
                        http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Orders/"+str(user.id)+"/"+str(order.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                res = super(SaleOrder, self).action_confirm()
                return res

class ButtonStockPickingValidate(models.Model):
        _inherit = 'stock.picking'

        def button_validate(self):
                http_request = None
                http_request = urllib3.PoolManager()
                encoded_body = None
                user = None
                for orderr in self:
                        sorders = self.env['sale.order'].sudo().search([])
                        for so in sorders:
                                if orderr.origin == so.name:
                                        partner = self.env['res.partner'].sudo().search([('parent_id.id','!=',False)])
                                        partners = []
                                        for i in partner:
                                                partners.append(i.id)
                                        if orderr.partner_id.id in partners:
                                                current_id = orderr.partner_id.parent_id.id
                                                user = self.env['res.users'].sudo().search([('partner_id.id','=',current_id)])
                                        else:
                                                user = self.env['res.users'].sudo().search([('partner_id.id','=',orderr.partner_id.id)])
                                        encoded_body = json.dumps({"read":False,"order_nb":so.name,"time":int(round(datetime.datetime.now().timestamp())),"status":"Delivered","email":orderr.partner_id.email})
                                        http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Orders/"+str(user.id)+"/"+str(so.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                res = super(ButtonStockPickingValidate,self).button_validate()
                return res
       
class OnTheWay(models.Model):
    _inherit = 'stock.picking'

    def on_the_way(self):
        http_request = None
        http_request = urllib3.PoolManager()
        encoded_body = None
        for orderr in self:
                orderr.write({
                      'state':'on_the_way'  
                })
                sorders = self.env['sale.order'].sudo().search([])
                for so in sorders:
                        if orderr.origin == so.name:
                                partner = self.env['res.partner'].sudo().search([('parent_id.id','!=',False)])
                                partners = []
                                for i in partner:
                                        partners.append(i.id)
                                if orderr.partner_id.id in partners:
                                        current_id = orderr.partner_id.parent_id.id
                                        user = self.env['res.users'].sudo().search([('partner_id.id','=',current_id)])
                                else:
                                        user = self.env['res.users'].sudo().search([('partner_id.id','=',orderr.partner_id.id)])
                                encoded_body = json.dumps({"order_nb":so.name,"read":False,"time":int(round(datetime.datetime.now().timestamp())),"status":"On the Way","email":orderr.partner_id.email})
                                http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Orders/"+str(user.id)+"/"+str(so.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})

class ButtonCancel(models.Model):
        _inherit = 'sale.order'

        def action_cancel(self):
                http_request = None
                http_request = urllib3.PoolManager()
                encoded_body = None
                user = None
                for order in self:
                        order.write({
                                "state":"cancel"
                        })
                        partner = self.env['res.partner'].sudo().search([('parent_id.id','!=',False)])
                        partners = []
                        for i in partner:
                                partners.append(i.id)
                        if order.partner_id.id in partners:
                                current_id = order.partner_id.parent_id.id
                                user = self.env['res.users'].sudo().search([('partner_id.id','=',current_id)])
                        else:
                                user = self.env['res.users'].sudo().search([('partner_id.id','=',order.partner_id.id)])
                        encoded_body = json.dumps({"read":False,"order_nb":order.name,"time":int(round(datetime.datetime.now().timestamp())),"status":"Cancelled","email":order.partner_id.email})
                        http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Orders/"+str(user.id)+"/"+str(order.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                res = super(SaleOrder, self).action_cancel()
                return res

class StockPicking(models.Model):
        _inherit = 'stock.picking'

        state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Order Received'),
        ('assigned', 'Packaging'),
        ('on_the_way', 'On the Way'),
        ('done', 'Delivered'),
        ('cancel', 'Cancelled')
        ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True)

class Expenses(models.Model):
       _inherit = 'hr.expense'

       exp_nb = fields.Integer(string="Expense Nb")
       vendor = fields.Many2one('res.partner',string="Vendor")

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    received = fields.Boolean(string='Received')

class RatingProduct(models.Model):
    _name = 'rating.product'

    user_id = fields.Many2one('res.users', string='User')
    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.template', string='Product')
    rating = fields.Float()

class VerifyUser(models.Model):
        _name = 'verify.user'

        mobile = fields.Char()
        code = fields.Integer()
        time = fields.Datetime()
        counter = fields.Integer()
        expired = fields.Boolean()

        def update_code_expiry(self):
                verify_users = self.env['verify.user'].search([])
        
                # Define the maximum allowed time difference in minutes (2 minutes in this case)
                max_time_difference = datetime.timedelta(minutes=1,seconds=30)
                
                current_time = datetime.datetime.now()
                
                for verify_user in verify_users:
                        # Calculate the time difference between the current time and the record's time field
                        time_difference = current_time - verify_user.time
                        
                        # If the time difference is greater than or equal to the maximum allowed time difference
                        if time_difference >= max_time_difference:
                                # Reset the counter field to 0
                                verify_user.sudo().write({'expired': True})
        
        def refresh_verify_counter(self):
                verify_users = self.env['verify.user'].search([])
        
                # Define the maximum allowed time difference in minutes (2 minutes in this case)
                max_time_difference = datetime.timedelta(hours=12)
                
                current_time = datetime.datetime.now()
                
                for verify_user in verify_users:
                        # Calculate the time difference between the current time and the record's time field
                        time_difference = current_time - verify_user.time
                        
                        # If the time difference is greater than or equal to the maximum allowed time difference
                        if time_difference >= max_time_difference:
                                # Reset the counter field to 0
                                verify_user.sudo().write({'counter': 0})
