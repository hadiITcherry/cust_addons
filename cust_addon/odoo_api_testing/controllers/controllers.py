import json
import time
from odoo import http
import math
import urllib3
import datetime
import hashlib
import random
import requests

class OdooApiTesting(http.Controller): 
    
    ### Change Password
    @http.route('/api/changePassword',auth='none',type='http',csrf=False,methods=['POST'])
    def change_password(self,**kw):
        try:
            if (http.request.session.uid != None):
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    new_password = value['new_password']
                    current_password = value['current_password']
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                uid = http.request.session.authenticate("odoo_db", user.email, current_password)
                if uid:
                    for u in user:
                        u.write({
                            "password":new_password
                        })
                    return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'result':{'status':'Successfully Changed Password'}}),headers = {"content-type":"application/json"})
                else:
                    return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':'Incorrect Password'}),headers = {"content-type":"application/json"})
            else:
                return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':'Session expired'}),headers = {"content-type":"application/json"})    
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':"Wrong Credentials"}),headers = {"content-type":"application/json"})    
    
    ### Reset Password
    @http.route('/api/resetPassword', auth='none',type='http',csrf=False,methods=['POST'])
    def reset_password(self,**kw):
        try:
            new_password = None
            mobile = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                new_password = value['new_password']
                mobile = value['mobile']
            user = http.request.env['res.users'].sudo().search([('partner_id.mobile','=',mobile)])
            if user:
                for u in user:
                    u.write({
                        "password":new_password
                    })
                return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'result':{'status':'Successfully Changed Password'}}),headers = {"content-type":"application/json"})             
            else:
                return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':'Phone number not found'}),headers = {"content-type":"application/json"})
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':str(e)}),headers = {"content-type":"application/json"})    
  
    #### Register User
    @http.route('/api/register', auth='public',type='http',csrf=False,methods=['POST'])
    def register(self,**kw):
        try:
            user_password = None
            email = None
            name = None
            mobile = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                user_password = value['password']
                email = value['login']
                name = value['name']
                if (value.get('mobile')):
                    mobile = value['mobile']
            if http.request.env["res.users"].sudo().search([("login", "=", email)]):
                return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":"Failed, user already exist!"}),headers = {'content-type':'application/json'})
            if http.request.env["res.users"].sudo().search([("mobile", "=", mobile)]):
                    return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":"Failed, mobile number already exist!"}),headers = {'content-type':'application/json'})       
            user = http.request.env['res.users'].sudo().create({
                    'name':name,
                    'password':user_password,
                    'login':email,
                })
            user_id = user.partner_id.id
            user_details = http.request.env['res.partner'].sudo().search([('id','=',user_id)])
            for user in user_details:
                user.write({
                    "mobile":mobile,
                    "email":email
                })
            return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Registered User"}}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})

    ### login user
    @http.route('/api/login', type='http', auth="none",csrf=False,methods=["POST"])        
    def authenticate(self,**kw):
        try:
            password = None
            email = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                    password = value['password']
                    email = value['login']
            http.request.session.authenticate("odoo_db", email, password)
            user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
            cart = http.request.env['cart'].sudo().search([('partner_id.id','=',user.partner_id.id)])
            wishlist = http.request.env['wishlist'].sudo().search([('partner_id.id','=',user.partner_id.id)])
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{
                "vip":user.partner_id.is_vip,
                "have_items_in_cart":True if cart else False,
                "have_items_in_wishlist":True if wishlist else False,
                "partner_id":user.partner_id.id,
                "user_id":user.id,
                "name":user.partner_id.name,
                "email":user.partner_id.email,
                "mobile":user.partner_id.mobile if user.partner_id.mobile else "",
                "dob":str(user.partner_id.dob) if user.partner_id.dob else "",
                "image":('https://quico-odoo.net/web/image/res.partner/%s/image_1920' % user.partner_id.id) if (user.partner_id.image_1920) else ""
            }}),headers = {'content-type':'application/json'})  
        except Exception as e:
            return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
             
    ### Logout
    @http.route('/api/logout', type='http', auth="none",csrf=False)
    def destroy(self):
        headers = {'Content-Type':'application/json'}
        try:
            if (http.request.session.uid != None):
                http.request.session.logout()
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'status':'Logged out'}}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'status':'Session expired'}}), headers=headers)
        except Exception as e:
             return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
    
    ### Update user info 
    @http.route('/api/updateUserInfo',auth="none" , type='http',csrf=False,methods=['PUT','POST'])
    def update_user_info(self,**kw):
        try:
            if(http.request.session.uid != None):
                image = None
                dob = None
                name = None
                json_object = json.loads(http.request.httprequest.data)
                user_data = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                digit_set = set()
                url = ''
                value = ''
                data = {}
                for key,value in json_object.items():
                    if (value.get('name')):
                        name = value['name']
                    else:
                        name = user_data.partner_id.name
                    if (value.get('image')):
                        image = value['image']
                    else:
                        image = None
                    if (value.get('dob')):
                        dob = value['dob']
                    else:
                        dob = user_data.partner_id.dob
                for record in user_data:
                    record.write({
                        "name":name,
                     })
                    partner = http.request.env['res.partner'].sudo().search([('id','=',record.partner_id.id)])
                    for p in partner:
                        p.write({
                            "dob":dob,
                            "image_1920":image if image else False
                        })
                        if (image):
                            value = 'succ'
                            digits = ''.join(filter(str.isdigit, str(p['image_1920'].decode())))
                            unique_digits = ''.join(set(digits))
                            unique_digits = unique_digits[:5]
                            image_hash = hashlib.md5(p['image_1920']).hexdigest()
                            if (unique_digits, image_hash) not in digit_set:
                                digit_set.add((unique_digits, image_hash))
                                url = 'https://quico-odoo.net/web/image/res.partner/%s/image_1920/%s' % (p.id,  image_hash)
                                url += '?%s' % unique_digits
                            data = {
                                "name":user_data.partner_id.name,
                                "dob":str(user_data.partner_id.dob) if user_data.partner_id.dob else "",
                                "image":url,
                                "status":"Successfully Updated User Info"
                            }
                        else:
                            data = {
                                "name":user_data.partner_id.name,
                                "dob":str(user_data.partner_id.dob) if user_data.partner_id.dob else "",
                                "image":None,
                                "status":"Successfully Updated User Info"
                            }
                return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"result":data}),headers = {'content-type':'application/json'})
            else:
                return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
    
    ### Update Email Address
    @http.route('/api/updateEmail',auth="none" , type='http',csrf=False,methods=['PUT','POST'])
    def update_email(self,**kw):
        try:
            if(http.request.session.uid != None):
                email = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    email = value['email']
                user_data = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                if http.request.env["res.users"].sudo().search([("login", "=", email)]):
                    return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":"Failed, user already exist!"}),headers = {'content-type':'application/json'})       
                for record in user_data:
                    record.write({
                        "login":email,
                     })
                    partner = http.request.env['res.partner'].sudo().search([('id','=',record.partner_id.id)])
                    for p in partner:
                        p.write({
                            "email":email,
                        })
                return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Updated Email Address"}}),headers = {'content-type':'application/json'})
            else:
                return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
    
    ### Update Phone Number
    @http.route('/api/updateMobile',auth="none" , type='http',csrf=False,methods=['PUT','POST'])
    def update_mobile_number(self,**kw):
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id',"=",http.request.session.uid)])        
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    mobile = value['mobile']
                if http.request.env["res.users"].sudo().search([("mobile", "=", mobile)]):
                    return http.Response (json.dumps({"jsonrpc":"2.0","id":None,"error":"Failed, mobile number already exist!"}),headers = {'content-type':'application/json'})       
                for record in user:
                    partner = http.request.env['res.partner'].sudo().search([('id','=',user.partner_id.id)])
                    for p in partner:
                        p.write({
                            "mobile":mobile,
                        })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Updated Mobile Number"}}),headers = {'content-type':'application/json'}) 
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers = {'content-type':'application/json'}) 
        except Exception as e:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'}) 
    
    ### Product
    @http.route('/api/getAllProducts', auth='public',type="http",csrf=False,methods=['POST'],website=True)
    def get_products_filtered(self,**kw):
        try:
            page_number = 0
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                page_number = value['page']
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            total_products = http.request.env['product.template'].sudo().search([('detailed_type','=','product')])
            total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page) 
            products = http.request.env['product.template'].sudo().search([('detailed_type','=','product')],offset=offset,limit=per_page)
            product_details = []
            pagination = {}
            for product in products:
                    digit_set = set()
                    for product in products:
                        digits = ''.join(filter(str.isdigit, str(product['image_1920'].decode())))
                        unique_digits = ''.join(set(digits))
                        unique_digits = unique_digits[:5]
                        image_hash = hashlib.md5(product['image_1920']).hexdigest()
                        if (unique_digits, image_hash) not in digit_set:
                            digit_set.add((unique_digits, image_hash))
                            url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                            url += '?%s' % unique_digits
                    product_details.append({
                            'id':product.id,
                            'name':product.name,
                            'is_vip':product.vip,
                            'is_on_sale':product.sale,
                            'regular_price':product.list_price,
                            'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                            'category':product.categ_id.name,
                            "image":url
                        })
            pagination = {
                "page":page_number if page_number > 0 else 1,
                "size":0 if product_details == [] else len(product_details),
                "total_pages":total_pages
            }
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"products":product_details,"pagination":pagination}}),headers = {'content-type':'application/json'}) 
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'}) 
    
    ### Get Product By id (single page)
    @http.route('/api/getProduct/<id>', auth='none',type='http',csrf=False,methods=['GET'])
    def get_products_by_id(self,id):
        headers = {'Content-Type': 'application/json'}
        try:
            products = http.request.env['product.template'].sudo().search([("id",'=',id)])
            product_details = {}
            status = None
            wishlist = None
            rated = None
            cart = None
            digit_set = set()
            imagess = []
            average_rate = 0
            total_rating = 0
            for product in products:
                if (http.request.session.uid != None):
                        user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                        wishlist = http.request.env['wishlist'].sudo().search(['&',('product_id.id','=',id),('partner_id.id','=',user.partner_id.id)])
                        cart = http.request.env['cart'].sudo().search(['&',('product_id.id','=',id),('partner_id.id','=',user.partner_id.id)])
                        rated = http.request.env['rating.product'].sudo().search(['&',('product_id.id','=',id),('user_id.id','=',user.id)])
                attributes = http.request.env['product.template.attribute.value'].sudo().search([('product_tmpl_id.id','=',product.id)])
                images = http.request.env['product.image'].sudo().search([('product_tmpl_id.id','=',product.id)])
                rating = http.request.env['rating.product'].sudo().search([('product_id','=',product.id)])
                for rate in rating:
                    total_rating += int(rate.rating)
                average_rate = total_rating / len(rating) if len(rating) > 0 else 0.0
                for img in images:
                    if (img.image_1920):
                        digits = ''.join(filter(str.isdigit, str((img.image_1920).decode())))
                        unique_digits = ''.join(set(digits))[:5]
                        image_hash = hashlib.md5((img.image_1920)).hexdigest()
                        if (unique_digits, image_hash) not in digit_set:
                            digit_set.add((unique_digits, image_hash))
                            url = 'https://quico-odoo.net/web/image/product.image/%s/image_1920/%s' % (img.id,  image_hash)
                            url += '?%s' % unique_digits
                            imagess.append(url)
                if product.qty_available <= 0:
                    status = False
                else:
                    status = True
                product_details={
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'is_in_wishlist':True if wishlist else False,
                    'is_vip_charge_product':True if product.name == "vip charge" else False,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'quantity':int(cart.quantity) if cart else 0,
                    'quantity_available':int(product.qty_available),
                    'in_stock':status,
                    'rating':average_rate,
                    'rated_by_user':True if rated else False,
                    'description':product.description_sale if product.description_sale else "",
                    "specifications":[{"name":att.attribute_id.name,"value":att.name} for att in attributes],
                    'images':imagess
                }
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":product_details}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)
     
    ### Search Products
    @http.route('/api/search', auth='public',type='http',csrf=False,methods=['POST'])
    def search(self,**kw):
        try:
            product_name = ""
            page_number = 0
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                page_number = value['page']
                product_name = value['name']
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type",'=',"product")],limit=per_page,offset=offset)
            total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('detailed_type','=','product')])
            total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            product_details = []
            pagination ={}
            digit_set = set()
            url = ''
            for product in products:
                brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])

                if (product.image_1920):
                    digits = ''.join(filter(str.isdigit, str((product.image_1920).decode())))
                    unique_digits = ''.join(set(digits))[:5]
                    image_hash = hashlib.md5((product.image_1920)).hexdigest()
                    if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                        url += '?%s' % unique_digits
                product_details.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_values.name if brand_values else "",
                    "image":url
                })
            pagination = {
                    "page":page_number if page_number > 0 else 1,
                    "size":0 if product_details == [] else len(product_details),
                    "total_pages":total_pages
                }
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"products":product_details,"pagination":pagination}}),headers = {'content-type':'application/json'}) 
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'}) 
    
    ### Get all categories
    @http.route('/api/getCategories',auth='public',type='http',csrf=False,methods=['GET'])
    def get_Categories(self):
        headers = {'Content-Type':"application/json"}
        try:
            category = http.request.env['product.category'].sudo().search(['&',("id","!=",1),('id','!=',89)],order='priority asc')
            categories = []
            digit_set = set()
            for cat in category:
                if (cat.image):
                    digits = ''.join(filter(str.isdigit, str((cat.image).decode())))
                    unique_digits = ''.join(set(digits))[:5]
                    image_hash = hashlib.md5((cat.image)).hexdigest()
                    if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.category/%s/image/%s' % (cat.id,  image_hash)
                        url += '?%s' % unique_digits
                if cat.parent_id.id == False and cat.product_count != 0:
                        categories.append({
                            "id":cat.id,
                            "name":cat.name,
                            "priority":cat.priority,
                            "image":url
                        })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":categories}), headers=headers)
        except Exception as e:
            headers = {'Content-Type':"application/json"}
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'error':str(e)}}), headers=headers)
    
    ### Get Subcategories by Category
    @http.route('/api/getSubcategoriesByCategory/<id>',auth='public',type='http',csrf=False,methods=['GET'])
    def get_products_by_category(self,id,**kw):
        try:
            sub_category = http.request.env['product.category'].sudo().search([("parent_id.id",'=',id)])
            categories = []
            for categ in sub_category:
                categories.append({
                    "id":categ.id,
                    "name":categ.name,
                })
            categories.insert(0,{
                "id":1,
                "name":"All"
            })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":categories}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
    
    ### Get Product by Subcategory 
    @http.route('/api/getProductsBySubcategory',auth='public',type='http',csrf=False,methods=['POST'])
    def get_products_by_subcategory(self,**kw):
        try:
            products_list = []
            page_number = 0
            json_object = json.loads(http.request.httprequest.data)
            category_id = None
            sub_categ_id = None
            product_name = ""
            digit_set = set()
            for key,value in json_object.items():
                if(value.get('name')):
                    product_name = value['name']
                category_id = value['category_id']
                page_number = value['page']
                if (value.get('subcategory_id')):
                    sub_categ_id = value['subcategory_id']
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            pagination = {}
            if (sub_categ_id != None):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("categ_id.id","=",sub_categ_id),('detailed_type', '=', 'product')],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("categ_id.id","=",sub_categ_id),('detailed_type', '=', 'product')])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            else:
                category = http.request.env['product.category'].sudo().search([("parent_id.id",'=',category_id)]).ids
                category_ids = []
                for i in category:
                    category_ids.append(i)
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("categ_id.id","in",category_ids),('detailed_type', '=', 'product')],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("categ_id.id","in",category_ids),('detailed_type','=','product')])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            for product in products:
                brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])
                brand_value = brand_values[0] if brand_values else None
                if (product.image_1920):
                    digits = ''.join(filter(str.isdigit, str((product.image_1920).decode())))
                    unique_digits = ''.join(set(digits))[:5]
                    image_hash = hashlib.md5((product.image_1920)).hexdigest()
                    if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                        url += '?%s' % unique_digits
                products_list.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_value.name if brand_value else "",
                    'image':url
                })
            pagination = {
                    "page":page_number if page_number > 0 else 1,
                    "size":0 if products_list == [] else len(products_list),
                    "total_pages":total_pages
                }
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"products":products_list,"pagination":pagination}}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
    
    ### Get all brands 
    @http.route('/api/getBrands',auth='public',type='http',csrf=False,methods=['GET'])
    def get_brands(self):
        headers = {'Content-Type':"application/json"}
        try:
            brand = http.request.env['product.attribute'].sudo().search([('name','=',"BRAND")])
            brands = []
            for brand in brand:
                brand_values = http.request.env['product.attribute.value'].sudo().search([('attribute_id.id','=',brand.id)])
                for b in brand_values:
                    # check if the brand has products associated with it
                    product_templates = http.request.env['product.template.attribute.value'].sudo().search([('attribute_id','=',brand.id),('product_attribute_value_id','=',b.id)])
                    if product_templates:
                        url = None
                        if (b.image):
                            digits = ''.join(filter(str.isdigit, str((b.image).decode())))
                            unique_digits = ''.join(set(digits))[:5]
                            image_hash = hashlib.md5((b.image)).hexdigest()
                            url = 'https://quico-odoo.net/web/image/product.attribute.value/%s/image/%s' % (b.id,  image_hash)
                            url += '?%s' % unique_digits
                        brands.append({
                            "id":b.id,
                            "name":b.name,
                            "image":url
                        })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":brands}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)

    
    ### Get brands by id
    @http.route('/api/getSubcategoriesByBrand/<id>',auth='public',type='http',csrf=False,methods=['GET'])
    def get_products_by_brand(self,id,**kw):
        try:
            categories = []
            brands = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_attribute_value_id.id','=',id),('attribute_id.name','=',"BRAND")])
            brandss = []
            for b in brands:
                brandss.append(b.product_tmpl_id.id)
            product_category = http.request.env['product.template'].sudo().search(['&',('id','in',brandss),("detailed_type","=","product")])
            category_ids = []
            for p in product_category:
                category_ids.append(p.categ_id.id)
            category = http.request.env['product.category'].sudo().search([("id",'in',category_ids)])
            for categ in category:
                categories.append({
                    'id':categ.id,
                    'name':categ.name
                })
            categories.insert(0,{
                "id":1,
                "name":"All"
            })
            unique = list({ each['id'] : each for each in categories }.values())
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":unique}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})
    
    ### Get Products by Category from Brand
    @http.route('/api/getProductsByBrandSubcategory',auth='public',type='http',csrf=False,methods=['POST'])
    def get_products_by_categ_in_brand(self,**kw):
        try:
            categ_id = None
            brand_id = None
            page_number = 0
            product_name = ""
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                    if(value.get('name')):
                        product_name = value['name']
                    brand_id = value['brand_id']
                    if (value.get('subcategory_id')):
                        categ_id = value['subcategory_id']
                    page_number = value['page']
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            products = []
            pagination={}
            digit_set = set()
            brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_attribute_value_id.id','=',brand_id),('attribute_id.name','=',"BRAND")])
            brands = []
            for b in brand_values:
                brands.append(b.product_tmpl_id.id)
            if (categ_id != None):
                product = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('id','in',brands),('categ_id.id','=',categ_id),("detailed_type","=","product")],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('id','in',brands),('categ_id.id','=',categ_id),("detailed_type","=","product")])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            else:
                product = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('id','in',brands),("detailed_type","=","product")],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('id','in',brands),("detailed_type","=","product")])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            for product in product:
                brand_value = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])

                if (product.image_1920):
                    digits = ''.join(filter(str.isdigit, str((product.image_1920).decode())))
                    unique_digits = ''.join(set(digits))[:5]
                    image_hash = hashlib.md5((product.image_1920)).hexdigest()
                    if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                        url += '?%s' % unique_digits
                products.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_value.name if brand_value else "",
                    'image':url
                })
            pagination = {
                    "page":page_number if page_number > 0 else 1,
                    "size":0 if products == [] else len(products),
                    "total_pages":total_pages
                }
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"products":products,"pagination":pagination}}),headers = {'content-type':'application/json'})
        except Exception as e:
             return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'})

    ### Order Details
    @http.route('/api/getDeliveryOrders',auth='none',type='http',csrf=False,methods=['GET'],)
    def get_order_details(self):
        headers = {'Content-Type': 'application/json'}
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                partner = http.request.env['res.partner'].sudo().search([('parent_id.id','=',user.partner_id.id)]).ids
                orders = http.request.env['sale.order'].sudo().search(["|",("partner_id.id",'=',user.partner_id.id),('partner_id.id','in',partner)],order="date_order desc") 
                order_list = []
                for order in orders:
                    stock = http.request.env['stock.picking'].sudo().search([('origin','ilike',order.name)])
                    scheduled_date = order.date_order.strftime("%Y-%m-%d %H:%M:%S") if order.date_order else ""
                    order_list.append({
                        'id':order.id,
                        'order_nb':order.name,
                        'status':"Packaging" if stock.state == "assigned" else "On the Way" if stock.state == "on_the_way" else "Delivered" if stock.state == "done" else "Cancelled" if stock.state == "cancel" else "Order Received",
                        "total":round(order.amount_total,3),
                        'date':scheduled_date,
                        }) 
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":order_list}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':'Session expired'}), headers=headers)
        except Exception as e:
               return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)

    ### Order Details by Id
    @http.route('/api/getDeliveryOrder/<id>',auth='none',type='http',csrf=False,methods=['GET'],)
    def get_order_details_by_id(self,id):
        headers = {'Content-Type': 'application/json'}
        try:
            if (http.request.session.uid != None):
                orders = http.request.env['sale.order'].sudo().search([('id','=',id)]) 
                order_list = {}
                if orders:
                    for order in orders:
                        order_lines = http.request.env['sale.order.line'].sudo().search([('order_id.id','=',order.id)])
                        stock = http.request.env['stock.picking'].sudo().search([('origin','ilike',order.name)])
                        scheduled_date = order.date_order.strftime("%Y-%m-%d %H:%M:%S") if order.date_order else ""
                        scheduled_done = stock.date_done.strftime("%Y-%m-%d %H:%M:%S") if stock.date_done else ""
                        order_list = {
                            'id':order.id,
                            'order_nb':order.name,
                            'status':"Packaging" if stock.state == "assigned" else "On the Way" if stock.state == "on_the_way" else "Delivered" if stock.state == "done" else "Cancelled" if stock.state == "cancel" else "Order Received",
                            "created_date":scheduled_date,
                            "delivered_date":scheduled_done,
                            'payment_method':order.payment_method,
                            'address':{
                                'id':order.partner_id.id,
                                'name':order.partner_id.name,
                                'email':order.partner_id.email if (order.partner_id.email != False)  else "",
                                'street':order.partner_id.street if (order.partner_id.street != False)  else "",
                                'street2':order.partner_id.street2 if (order.partner_id.street != False)  else "",
                                'zip':order.partner_id.zip if (order.partner_id.zip != False)  else "",
                                'city':order.partner_id.city if (order.partner_id.city != False)  else "",
                                'mobile':order.partner_id.mobile if (order.partner_id.mobile != False)  else ""
                            },
                            'order_lines':[(dict(id=ol.product_id.product_tmpl_id.id,name=ol.name,quantity=int(ol.product_uom_qty),subtotal=ol.price_subtotal)) for ol in order_lines],
                            "total_without_vat":round(order.amount_untaxed,2),
                            "VAT_percentage":"11%",
                            "VAT_amount":order.amount_tax,
                            "total":round(order.amount_total,2)
                            }   
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":order_list}), headers=headers)
                else:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"No Order Found"}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers=headers)
        except Exception as e:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)

    ### Add to cart 
    @http.route('/api/addToCart', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def add_to_cart(self,**kw):
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id',"=",http.request.session.uid)])
                product_id = None
                quantity = None
                is_vip_price = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    product_id = value['product_id']
                    quantity = value['quantity']
                    if (quantity < 0):
                        return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Negative Not Accepted"}), headers={'content-type':'application/json'})
                    if (value.get('is_vip_price')):
                        is_vip_price = value['is_vip_price']
                product = http.request.env['cart'].sudo().search(['&',('partner_id.id','=',user.partner_id.id),('product_id.id','=',product_id)])
                if user.partner_id.is_vip == True:
                        if product:
                                product.write({
                                    "quantity":product.quantity + quantity
                                })
                        else:
                            http.request.env['cart'].with_user(user.id).create({
                                    'partner_id': user.partner_id.id,
                                    'product_id': product_id,
                                    "quantity":quantity,
                        })
                else:      
                    if is_vip_price != True or is_vip_price == "":
                        if product:
                            product.write({
                                "quantity":product.quantity + quantity
                            })
                        else:
                            http.request.env['cart'].with_user(user.id).create({
                                    'partner_id': user.partner_id.id,
                                    'product_id': product_id,
                                    "quantity":quantity,
                                })
                    else:
                        product_with_vip = http.request.env['cart'].sudo().search(['&',('partner_id.id','=',user.partner_id.id),("product_id.name",'ilike',"vip charge")])
                        vip_charge = http.request.env['product.template'].sudo().search([('name','ilike','vip charge')])
                        if product_with_vip:
                            if product:
                                    product.write({
                                        "quantity":product.quantity + quantity
                                    })
                            else:
                                    http.request.env['cart'].with_user(user.id).create({
                                            'partner_id': user.partner_id.id,
                                            'product_id': product_id,
                                            "quantity":quantity,
                                    })
                        else:
                            partner = http.request.env['res.partner'].sudo().search([('parent_id.id','=',user.partner_id.id)]).ids
                            orders = http.request.env['stock.picking'].sudo().search(["&",('state','!=','cancel'),"|",("partner_id.id",'=',user.partner_id.id),('partner_id.id','in',partner)]) 
                            canceled_orders = http.request.env['stock.picking'].sudo().search(["&",('state','ilike','cancel'),"|",("partner_id.id",'=',user.partner_id.id),('partner_id.id','in',partner)]) 
                            can_add_vip = False
                            products = []
                            products_in_cancel = []
                            print (canceled_orders)
                            print(orders)
                            if canceled_orders and not orders:
                                for co in canceled_orders:
                                    order_liness = http.request.env['sale.order.line'].sudo().search([('order_id.name','=',co.origin)])
                                    for oll in order_liness:
                                        products_in_cancel.append(oll.name)
                                        if "vip charge" in products_in_cancel:
                                            can_add_vip = True
                            elif not canceled_orders and orders:
                                for o in orders:
                                    order_line = http.request.env['sale.order.line'].sudo().search([('order_id.name','=',o.origin)])
                                    for ol in order_line:
                                        products.append(ol.name)
                                        if "vip charge" in products:
                                            can_add_vip = False
                                        else:
                                            can_add_vip = True
                            elif canceled_orders and orders:
                                for o in orders:
                                    order_line = http.request.env['sale.order.line'].sudo().search([('order_id.name','=',o.origin)])
                                    for ol in order_line:
                                        products.append(ol.name)
                                        if "vip charge" in products:
                                            can_add_vip = False
                                        else:
                                            can_add_vip = True
                            else:
                                    can_add_vip = True
                            print(products_in_cancel)
                            print (products)    
                            print (can_add_vip)
                            if (can_add_vip == True):
                                http.request.env['cart'].with_user(user.id).create({
                                        'partner_id': user.partner_id.id,
                                        'product_id': vip_charge.id,
                                        "quantity":1,
                                    })
                                if product:
                                    product.write({
                                        "quantity":product.quantity + quantity
                                    })
                                else:
                                    http.request.env['cart'].with_user(user.id).create({
                                            'partner_id': user.partner_id.id,
                                            'product_id': product_id,
                                            "quantity":quantity,
                                    })
                            else:
                                    if product:
                                        product.write({
                                            "quantity":product.quantity + quantity
                                        })
                                    else:
                                        http.request.env['cart'].with_user(user.id).create({
                                                'partner_id': user.partner_id.id,
                                                'product_id': product_id,
                                                "quantity":quantity,
                                    })
                cart = http.request.env['cart'].sudo().search([('partner_id.id','=',user.partner_id.id)])
                have_items_in_cart = True if cart else False
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'have_items_in_cart':have_items_in_cart,"status":"Successfully Added to Cart"}}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
                 return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})

    ### View Cart
    @http.route('/api/viewCart',auth="none",type="http",csrf=False,methods=["GET"])
    def view_cart(self):
        headers = {"content-type":"application/json"}
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                cart_list = http.request.env['cart'].sudo().search([('partner_id.id',"=",user.partner_id.id)])
                cart_data = []
                status = None
                digit_set = set()
                for cart in cart_list:
                    product = http.request.env['product.template'].sudo().search([("id",'=',cart.product_id.id)])
                    for p in product:
                        digits = ''.join(filter(str.isdigit, str(p['image_1920'].decode())))
                        unique_digits = ''.join(set(digits))
                        unique_digits = unique_digits[:5]
                        image_hash = hashlib.md5(p['image_1920']).hexdigest()
                        if (unique_digits, image_hash) not in digit_set:
                                digit_set.add((unique_digits, image_hash))
                                url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (p.id,  image_hash)
                                url += '?%s' % unique_digits
                        if p.qty_available <=0 and p.name != 'vip charge':
                            status = False
                        else:
                            status = True
                        cart_data.append({
                                "id":p.id,
                                "name":p.name,
                                'is_vip':p.vip,
                                'is_on_sale':p.sale,
                                'is_vip_charge_product':True if p.name == "vip charge" else False,
                                "regular_price":p.list_price,
                                "new_price":p.vip_price if p.vip == True else p.sale_price if p.sale == True else 0.0,
                                "quantity":int(cart.quantity),
                                "quantity_available":int(p.qty_available),
                                "in_stock":status,
                                "image":url
                            })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":cart_data}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'error':'Session expired'}}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'error':str(e)}}), headers=headers)
    
    ### Update Cart Quantity
    @http.route('/api/updateCartQuantity',auth="none",type="http",csrf=False,methods=["PUT","POST"])
    def update_cart_quantity(self,**kw):
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                json_object = json.loads(http.request.httprequest.data)
                quantity = None
                product_id = None
                cart = http.request.env['cart'].sudo().search([('partner_id.id','=',user.partner_id.id)])
                have_items_in_cart = True if cart else False
                for key,value in json_object.items():
                    product_id = value['product_id']
                    quantity = value['quantity']
                cart_list = http.request.env['cart'].sudo().search(['&',('partner_id.id',"=",user.partner_id.id),('product_id.id','=',product_id)])
                for record in cart_list:
                    record.write({
                        "quantity":quantity,
                    })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'have_items_in_cart':have_items_in_cart,"status":"Successfully Updated Quantity in Cart"}}),headers = {'content-type':'application/json'}) 
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers = {'content-type':'application/json'}) 
        except Exception as e:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'}) 
    
    ### Remove Product From Cart
    @http.route('/api/removeFromCart', auth='none',type='http',csrf=False,website=False,methods=['POST','DELETE'])
    def remove_from_cart(self,**kw):
        try:
            if (http.request.session.uid != None):
                product_id = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    product_id = value['product_id']
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                http.request.env['cart'].sudo().search(['&',('partner_id.id',"=",user.partner_id.id),('product_id.id','=',product_id)]).unlink()
                cart = http.request.env['cart'].sudo().search([('partner_id.id','=',user.partner_id.id)])
                have_items_in_cart = True if cart else False
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'have_items_in_cart':have_items_in_cart,'status':'Successfully Removed from Cart'}}), headers={'content-type':'application/json'})
            else:
                 return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':'Session expired'}), headers={'content-type':'application/json'})
        except Exception as e:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':'Session expired'}), headers={'content-type':'application/json'})

    ### Create Delivery Order
    @http.route('/api/deliveryOrder',auth="none",type="http",csrf=False,methods=["POST"])
    def create_delivery_order(self,**kw):
        try:
            if(http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id',"=",http.request.session.uid)])
                partner_shipping_id = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    partner_shipping_id = value['address_id']
                order = http.request.env['sale.order'].with_user(user.id).create({
                    'partner_id': partner_shipping_id,
                    'partner_invoice_id':partner_shipping_id,
                    'partner_shipping_id':partner_shipping_id,
                    'date_order':datetime.datetime.now(),
                    "website_id":1,
                    "company_id":user.company_id.id,
                })
                order_id = order.id
                order_lines = []
                data = json.loads(http.request.httprequest.data)
                json_data = json.dumps(data)
                resp = json.loads(json_data)
                for i in resp['params']['order_lines']:
                    product_id = http.request.env['product.product'].sudo().search([('product_tmpl_id.id','=',i['product_id'])])
                    if i['is_vip_price'] == True:
                        order_lines.append({
                            "order_id":order_id,
                            "product_id":product_id.id,
                            "name":product_id.product_tmpl_id.name,
                            "price_unit":product_id.product_tmpl_id.vip_price if product_id.product_tmpl_id.vip == True else product_id.product_tmpl_id.sale_price if product_id.product_tmpl_id.sale == True else product_id.product_tmpl_id.list_price,
                            "product_uom_qty":i['quantity'],
                            "company_id":user.company_id.id,
                            "currency_id":user.company_id.currency_id.id
                        })
                    else:
                        order_lines.append({
                        "order_id":order_id,
                        "product_id":product_id.id,
                        "name":product_id.product_tmpl_id.name,
                        "price_unit":product_id.product_tmpl_id.list_price if product_id.product_tmpl_id.vip == True else product_id.product_tmpl_id.sale_price if product_id.product_tmpl_id.sale == True else product_id.product_tmpl_id.list_price,
                        "product_uom_qty":i['quantity'],
                        "company_id":user.company_id.id,
                        "currency_id":user.company_id.currency_id.id
                    })
                order_line = http.request.env['sale.order.line'].with_user(user.id).create(order_lines)
                empty_cart = http.request.env['cart'].sudo().search([('partner_id.id',"=",user.partner_id.id)]).unlink()
                http_request = None
                http_request = urllib3.PoolManager()
                encoded_body = json.dumps({"read":False,"order_nb":order.name,"time":int(round(datetime.datetime.now().timestamp())),"status":"Order Received"})
                http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Orders/"+str(user.id)+"/"+str(order_id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Created Delivery Order"}}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})

    ### Get Delivery Addresses
    @http.route('/api/getDeliveryAddresses',auth="none" , type='http',csrf=False,methods=['GET'])
    def get_addresses(self):
        headers = {'Content-Type': 'application/json'}
        try:
            if (http.request.session.uid != None):
                address = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                other = []
                for add in address:
                    child_address = http.request.env['res.partner'].sudo().search([('parent_id.id',"=",add.partner_id.id)])
                    for child in child_address:
                        other.append({
                            "id":child.id,
                            "name":child.name if (child.name != False) else "",
                            "street":child.street if (child.street != False) else "",
                            "street2":child.street2 if (child.street2 != False) else "",
                            "country":child.country_id.name if (child.country_id.name != False) else "",
                            "city":child.city if (child.city != False) else "",
                            "zip":child.zip if (child.zip != False) else "",
                            "mobile":child.mobile if (child.mobile != False) else "",
                        })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":other}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':"Session expired"}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)

    ### Get Delivery Addresses By Id
    @http.route('/api/getDeliveryAddresses/<id>',auth="none" , type='http',csrf=False,methods=['GET'])
    def get_addresses_by_id(self,id):
        headers = {'Content-Type': 'application/json'}
        try:
            if (http.request.session.uid != None):
                address = http.request.env['res.partner'].sudo().search([('id','=',id)])
                main={}
                for add in address:
                    main = {
                            "id":add.id,
                            "name":add.name if (add.name != False) else "",
                            "street":add.street if (add.street != False) else "",
                            "street2":add.street2 if (add.street2 != False) else "",
                            "country":add.country_id.name if (add.country_id.name != False) else "",
                            "city":add.city if (add.city != False) else "",
                            "zip":add.zip if (add.zip != False) else "",
                            "mobile":add.mobile if (add.mobile != False) else "",
                        }
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":main}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)

    ### Update Delivery Address
    @http.route('/api/updateDeliveryAddress/<id>',auth="none" , type='http',csrf=False,methods=['PUT','POST'])
    def update_address(self,id,**kw):
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.partner'].sudo().search([('id',"=",id)])
                name = None
                street = None
                street2 = None
                city = None
                zip = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    if (value.get('name')):
                        name = value['name']
                    else:
                        name = user.name
                    if (value.get('street')):
                        street = value['street']
                    else:
                        street = user.street
                    if (value.get('street2')):
                        street2 = value['street2']
                    else:
                        street2 = user.street2
                    if (value.get('city')):
                        city = value['city']
                    else:
                        city = user.city
                    if (value.get('zip')):
                        zip = value['zip']
                    else:
                        zip = user.zip
                order = http.request.env['sale.order'].sudo().search([('partner_id.id','=',id)]).ids
                orders = []
                for i in order:
                    orders.append(i)
                if orders != []:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Cannot Update Delivery Address Since its Related to an Order"}), headers={'content-type':'application/json'})
                else:
                    for record in user:
                        record.write({
                            "name":name,
                            "street":street,
                            "street2":street2,
                            "city":city,
                            "zip":zip,
                        })
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'status':'Successfully Updated Delivery Address'}}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})

    ### Create Delivery Address
    @http.route('/api/createDeliveryAddress', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def create_delivery_address(self,**kw):
        try:
            if (http.request.session.uid != None):
                name = None
                street = None
                street2 = None
                city = None
                zip = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    if (value.get('name')):
                        name = value['name']
                    if (value.get('street')):
                        street = value['street']
                    if (value.get('street2')):
                        street2 = value['street2']
                    if (value.get('city')):
                        city = value['city']
                    if (value.get('zip')):
                        zip = value['zip']
                user = http.request.env['res.users'].sudo().search([('id',"=",http.request.session.uid)])
                http.request.env['res.partner'].with_user(user.id).create({
                        'parent_id': user.partner_id.id,
                        'type': "delivery",
                        "name":name,
                        "street":street,
                        "street2":street2,
                        "country_id":126,
                        "city":city,
                        "zip":zip,
                        "mobile":user.partner_id.mobile,
                        "email":user.partner_id.email
                    })
                partner = http.request.env['res.partner'].sudo().search([('id',"=",user.partner_id.id)])
                for p in partner:
                    p.write({
                        "street":street,
                        "street2":street2,
                        "country_id":126,
                        "city":city,
                        "zip":zip,
                        "phone":user.partner_id.mobile
                    })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'status':'Successfully Created Delivery Address'}}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})
    
    ### Remove Delivery Address
    @http.route('/api/removeDeliveryAddress', auth='none',type='http',csrf=False,website=False,methods=['POST','DELETE'])
    def remove_delivery_address(self,**kw):
        try:
            if(http.request.session.uid != None):
                id = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    id = value['id']
                order = http.request.env['sale.order'].sudo().search([('partner_id.id','=',id)]).ids
                orders = []
                for i in order:
                    orders.append(i)
                if orders != []:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Cannot Delete Delivery Address Since its Related to an Order"}), headers={'content-type':'application/json'})
                else:
                    http.request.env['res.partner'].sudo().search([('id',"=",id)]).unlink()
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'status':'Successfully Removed Delivery Address'}}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})
    
    ### Get service types
    @http.route('/api/getServiceTypes/<id>',auth="public" , type='http',csrf=False,methods=['GET'],website=True)
    def get_service_types_by_id(self,id):
        headers = {'Content-Type': 'application/json'}
        try:
            service_type = http.request.env['fsm.order.type'].sudo().search(['&',('parent_id','=',False),("service_id.id","=",id)],order = "priority asc")
            service_types = []
            digit_set = set()
            for serv in service_type:
                digits = ''.join(filter(str.isdigit, str(serv['image'].decode())))
                unique_digits = ''.join(set(digits))
                unique_digits = unique_digits[:5]
                image_hash = hashlib.md5(serv['image']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/fsm.order.type/%s/image/%s' % (serv.id,  image_hash)
                        url += '?%s' % unique_digits
                service_types.append({
                    "id":serv.id,
                    "type":serv.name,
                    "priority":serv.priority,
                    "image":url,
                    "have_sub_service":serv.have_sub
                })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":service_types}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)

    ### Get service types
    @http.route('/api/getSubServiceType/<id>',auth="public" , type='http',csrf=False,methods=['GET'])
    def get_sub_service_types_by_id(self,id,**kw):
        headers = {'Content-Type':'application/json'}
        try:
            sub_service_type = http.request.env['fsm.order.type'].sudo().search([("parent_id.id","=",id)],order='priority asc')
            sub_service_types = []
            digit_set = set()
            for serv in sub_service_type:
                digits = ''.join(filter(str.isdigit, str(serv['image'].decode())))
                unique_digits = ''.join(set(digits))
                unique_digits = unique_digits[:5]
                image_hash = hashlib.md5(serv['image']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/fsm.order.type/%s/image/%s' % (serv.id,  image_hash)
                        url += '?%s' % unique_digits
                sub_service_types.append({
                    "id":serv.id,
                    "type":serv.name,
                    "priority":serv.priority,
                    "have_sub_service":serv.have_sub,
                    "image":url
                })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":sub_service_types}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)

    ### get services 
    @http.route('/api/getServices',auth="public" , type='http',csrf=False,methods=['GET'])
    def get_service(self):
        headers = {'Content-Type': 'application/json'}       
        try:
            service = http.request.env['fsm.tag'].sudo().search([],order="priority asc")
            services = []
            digit_set = set()
            for serv in service:
                digits = ''.join(filter(str.isdigit, str(serv['icon'].decode())))
                unique_digits = ''.join(set(digits))
                unique_digits = unique_digits[:5]
                image_hash = hashlib.md5(serv['icon']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/fsm.tag/%s/icon/%s' % (serv.id,  image_hash)
                        url += '?%s' % unique_digits
                services.append({
                    "id":serv.id,
                    "name":serv.name,
                    "priority":serv.priority,
                    "have_service_type":serv.have_service_type,
                    "description":serv.description if serv.description != False else "",
                    "image":url
                })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":services}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)

    ### Repair Form
    @http.route('/api/createServiceOrder', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def service_order(self,**kw):
        try:
            if(http.request.session.uid != None):
                service = None
                service_type = None
                delivery_type = None
                description = None
                image_1 = None
                image_2 = None
                image_3 = None
                image_4 = None
                audio = None
                audio_filename = None
                address = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    if (value.get('address_id')):
                        address = value['address_id']
                    if (value.get('service_id')):
                        service = value['service_id']
                    if (value.get('service_type_id')):
                        service_type = value['service_type_id']
                    if (value.get('delivery_type')):
                        delivery_type = value['delivery_type']
                    if (value.get('description')):
                        description = value['description']
                    if (value.get('audio')):
                        audio = value.get('audio')
                    if (value.get('audio_filename')):
                        audio_filename = value.get('audio_filename')
                    if (value.get('images')):
                        if (len(value.get('images')) == 4):
                            image_1 = value.get("images")[0]
                            image_2 = value.get("images")[1]
                            image_3 = value.get("images")[2]
                            image_4 = value.get("images")[3]
                        elif (len(value.get("images")) == 3):
                            image_1 = value.get("images")[0]
                            image_2 = value.get("images")[1]
                            image_3 = value.get("images")[2]
                        elif (len(value.get("images")) == 2): 
                            image_1 = value.get("images")[0]
                            image_2 = value.get("images")[1]
                        elif (len(value.get("images")) == 1):
                            image_1 = value.get("images")[0]
                        else:
                            pass    
                #api_key = "AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"
                #check_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
                #check_data = {
                #"email": "odoo@firebase.com",
                #"password": "OdooFirebase",
                #"returnSecureToken": True
                #}
                #requests.post(check_url, json=check_data) 
                user = http.request.env['res.users'].sudo().search([('id',"=",http.request.session.uid)])
                service_order = http.request.env['fsm.order'].sudo().create({
                        'company_id':1,
                        'stage_id':1,
                        'team_id':1,
                        'partner_id': address if address else user.partner_id.id,
                        'service':[(4,service)],
                        'service_type': service_type,
                        'delivery_type':delivery_type,
                        'description':description,
                        'image_1':image_1,
                        'image_2':image_2,
                        'image_3':image_3,
                        'image_4':image_4,
                        'audio':audio,
                        'audio_file_name':audio_filename
                })
                http_request = None
                http_request = urllib3.PoolManager()
                encoded_body = json.dumps({"read":False,"time":int(round(datetime.datetime.now().timestamp())),"service_nb":service_order.name,"status":"Request Received"})
                http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Services/"+str(user.id)+"/"+str(service_order.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{'status':"Succefully Submitted Order"}}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})

    ### Get Service Orders
    @http.route('/api/getServiceOrders', auth='none',type='http',csrf=False,website=False,methods=['GET'])
    def get_service_order(self):
        headers = {"content-type":"application/json"}
        try:
            if(http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                partner = http.request.env['res.partner'].sudo().search([('parent_id.id','=',user.partner_id.id)]).ids
                service = http.request.env['fsm.order'].sudo().search(["|",("partner_id.id",'=',user.partner_id.id),("partner_id.id",'in',partner)],order="scheduled_date_start desc")
                service_orders = []
                for order in service:
                    scheduled_date = order.scheduled_date_start.strftime("%Y-%m-%d %H:%M:%S") if order.scheduled_date_start else ""
                    service_orders.append({
                            'id':order.id,
                            'service':order.service.name,
                            'service_nb':order.name,
                            'status':"Request Received" if order.stage_id.id == 1 else "Waiting Response" if order.stage_id.id == 4 else "In Progress" if order.stage_id.id == 5 else "Completed" if order.stage_id.id == 2 else "Cancelled" if order.stage_id.id == 3 else "",
                            'date':scheduled_date
                        })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":service_orders}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)

    ### Get Service Orders
    @http.route('/api/getServiceOrder/<id>', auth='none',type='http',csrf=False,website=False,methods=['GET'])
    def get_service_order_by_id(self,id):
        headers = {"content-type":"application/json"}
        try:
            if(http.request.session.uid != None):
                service = http.request.env['fsm.order'].sudo().search([('id',"=",id)])
                service_order = {}
                images = []
                if service:
                    for order in service:
                        scheduled_date = order.scheduled_date_start.strftime("%Y-%m-%d %H:%M:%S") if order.scheduled_date_start else ""
                        scheduled_end = order.scheduled_date_end.strftime("%Y-%m-%d %H:%M:%S") if order.scheduled_date_end else ""
                        address_dtd = {
                            "id": order.partner_id.id,
                            "name": order.partner_id.name,
                            "street": order.partner_id.street if order.partner_id.street != False else "",
                            "street2": order.partner_id.street2 if order.partner_id.street2 != False else "",
                            "city": order.partner_id.city if order.partner_id.city != False else "",
                            "zip": order.partner_id.zip if order.partner_id.zip != False else "",
                            "email": order.partner_id.email if order.partner_id.email != False else "",
                            "mobile": order.partner_id.mobile if order.partner_id.mobile != False else ""
                        }
                        address_quico = {
                            "id": 321,
                            "name": 'Quico Tech',
                            "street": 'Beirut',
                            "street2": 'Galerie Semaan',
                            "city": 'Beirut',
                            "zip": "2029",
                            "email": "info@quicotech.com",
                            "mobile": "+9613540504"
                        }
                        address = address_dtd if order.delivery_type == "dtd" else address_quico
                        if (order.image_1):
                            images.append('https://quico-odoo.net/web/image/fsm.order/%s/image_1' % order.id)
                        if (order.image_2):
                            images.append('https://quico-odoo.net/web/image/fsm.order/%s/image_2' % order.id)
                        if (order.image_3):
                            images.append('https://quico-odoo.net/web/image/fsm.order/%s/image_3' % order.id)
                        if (order.image_4):
                            images.append('https://quico-odoo.net/web/image/fsm.order/%s/image_4' % order.id)
                        service_order = {
                                'id':order.id,
                                'service_nb':order.name,
                                'service': order.service.name,
                                'service_type':order.service_type.name if order.service_type else None,
                                'status':"Request Received" if order.stage_id.id == 1 else "Waiting Response" if order.stage_id.id == 4 else "In Progress" if order.stage_id.id == 5 else "Completed" if order.stage_id.id == 2 else "Cancelled" if order.stage_id.id == 3 else "",
                                'delivery_type':order.delivery_type,
                                'address':address,
                                'problem_description':order.description if order.description != False else "",
                                'images':images,
                                'solution':order.resolution if order.resolution != False else "",
                                'scheduled_date_start':scheduled_date,
                                'scheduled_duration':str(order.scheduled_duration) if order.scheduled_duration != False else "",
                                'scheduled_date_end':scheduled_end
                            }
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":service_order}), headers=headers)
                else:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"No Service Order Found"}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)
    
    ### Apply Survey
    @http.route('/api/applySurvey', auth='user',type='http',csrf=False,website=False,methods=['POST','PUT'])
    def apply_survey(self):
        try:
            headers = {"content-type":"application/json"}
            if(http.request.session.uid != None):
                json_object = json.loads(http.request.httprequest.data)
                id = None
                review = None
                rating = None
                for key,value in json_object.items():
                    id = value.get('order_id')
                    if value.get('review'):
                        review = value.get('review')
                    if value.get('rating'):
                        rating = value.get('rating')
                order = http.request.env['sale.order'].sudo().search([('id','=',id)])
                for o in order:
                    o.write({
                        'review':review,
                        'order_rate':int(rating)
                    })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Succefully Submitted!"}}),headers=headers)     
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            headers = {"content-type":"application/json"}
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)     
    
    ### Notification Details
    @http.route('/api/notificationDetails', auth='user',type='http',csrf=False,website=False,methods=['POST','PUT'])
    def notification_details(self):
        try:
            headers = {"content-type":"application/json"}
            if(http.request.session.uid != None):
                json_object = json.loads(http.request.httprequest.data)
                id = None
                for key,value in json_object.items():
                    id = value.get('service_id')
                encoded_body = None
                service = http.request.env['fsm.order'].sudo().search([('id','=',id)])
                products = http.request.env['fsm.order.products'].sudo().search([('fsm_order_id.id','=',id)])
                situations = http.request.env['fsm.order.situation'].sudo().search([('fsm_order_id','=',id)])
                images = []
                if service:
                    if service.t_image_1:
                        images.append('https://quico-odoo.net/web/image/fsm.order/%s/t_image_1' % service.id)
                    if service.t_image_2:
                        images.append('https://quico-odoo.net/web/image/fsm.order/%s/t_image_2' % service.id)
                    if service.t_image_3:
                        images.append('https://quico-odoo.net/web/image/fsm.order/%s/t_image_3' % service.id)
                    if service.t_image_4:
                        images.append('https://quico-odoo.net/web/image/fsm.order/%s/t_image_4' % service.id)
                    if service.t_image_5:
                        images.append('https://quico-odoo.net/web/image/fsm.order/%s/t_image_5' % service.id)
                for s in service:
                    	encoded_body = {
                            "service_nb":s.name,
                            "situation":[(dict(name=st.fsm_situation_id.name,exist=st.exist)) for st in situations],
                            'products':[(dict(id=ol.product_id.id,name=ol.product_id.product_tmpl_id.name,quantity=int(ol.quantity),subtotal=ol.subtotal)) for ol in products],
                            'solution': s.resolution if s.resolution != False else "",
                            'scheduled_date_start':str(s.scheduled_date_start.strftime("%d-%m-%Y %H:%M:%S")) if s.scheduled_date_start != False else "",
                            'scheduled_date_end':str(s.scheduled_date_end.strftime("%d-%m-%Y %H:%M:%S")) if s.scheduled_date_end != False else "",
                            'duration':str(int(s.scheduled_duration))+" hours"  if s.scheduled_duration != False else "",
			    'images':images
                        }
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":encoded_body}),headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            headers = {"content-type":"application/json"}
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)     

    ### Accept Request
    @http.route('/api/acceptRequest', auth='user',type='http',csrf=False,website=False,methods=['POST','PUT'])
    def accept_request(self):
        try:
            if(http.request.session.uid != None):
                headers = {"content-type":"application/json"}
                http_request = None
                http_request = urllib3.PoolManager()
                json_object = json.loads(http.request.httprequest.data)
                id = None
                for key,value in json_object.items():
                    id = value.get('service_id')
                partner = http.request.env['res.partner'].sudo().search([('parent_id.id','!=',False)])
                products = []
                data = json.loads(http.request.httprequest.data)
                json_data = json.dumps(data)
                resp = json.loads(json_data)
                dtaa = []
                for i in resp['params']:
                        dtaa.append(i)
                if 'products' in dtaa:
                    for i in resp['params']['products']:
                        products.append(i['product_id'])
                partners = []
                user = None
                for i in partner:
                    partners.append(i.id)
                serv_order = http.request.env['fsm.order'].sudo().search([('id','=',id)])
                for serv in serv_order:
                    if serv.partner_id.id in partners:
                        current_id = serv.partner_id.parent_id.id
                        user = http.request.env['res.users'].sudo().search([('partner_id.id','=',current_id)])
                    else:
                        user = http.request.env['res.users'].sudo().search([('partner_id.id','=',serv.partner_id.id)])
                    encoded_body = json.dumps({"read":False,"time":int(round(datetime.datetime.now().timestamp())),"service_nb":serv.name,"status":"In Progress"})
                    http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Services/"+str(user.id)+"/"+str(serv.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                    serv.write({
                        'stage_id':5
                    }) 
                service_products = http.request.env['fsm.order.products'].sudo().search([('fsm_order_id.id','=',id)])
                for p in service_products:
                    if p.product_id.id in products:
                        p.write({
                            'chosen_product':True
                        })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Accepted!"}}),headers=headers)     
            else:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            headers = {"content-type":"application/json"}
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)     
        
    ### Reject Request
    @http.route('/api/rejectRequest', auth='user',type='http',csrf=False,website=False,methods=['POST','PUT'])
    def reject_request(self):
        try:
            if(http.request.session.uid != None):
                headers = {"content-type":"application/json"}
                http_request = None
                http_request = urllib3.PoolManager()
                json_object = json.loads(http.request.httprequest.data)
                id = None
                for key,value in json_object.items():
                    id = value.get('service_id')
                partner = http.request.env['res.partner'].sudo().search([('parent_id.id','!=',False)])
                partners = []
                user = None
                for i in partner:
                    partners.append(i.id)
                serv_order = http.request.env['fsm.order'].sudo().search([('id','=',id)])
                for serv in serv_order:
                    if serv.partner_id.id in partners:
                        current_id = serv.partner_id.parent_id.id
                        user = http.request.env['res.users'].sudo().search([('partner_id.id','=',current_id)])
                    else:
                        user = http.request.env['res.users'].sudo().search([('partner_id.id','=',serv.partner_id.id)])
                    encoded_body = json.dumps({"read":False,"time":int(round(datetime.datetime.now().timestamp())),"service_nb":serv.name,"status":"Cancelled"})
                    http_request.request("PUT", "https://quico-tech-default-rtdb.europe-west1.firebasedatabase.app/Services/"+str(user.id)+"/"+str(serv.id)+".json",body=encoded_body,headers={"content-type":"application/json","auth":"AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"})
                    serv.write({
                        'stage_id':3
                    }) 
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Rejected!"}}),headers=headers)     
            else:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            headers = {"content-type":"application/json"}
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)     
    
    ### Add to wishlist
    @http.route('/api/addToWishlist', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def add_to_wishlist(self,**kw):
        headers = {'content-Type':'application/json'}
        try:
            if(http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                product_id = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    product_id = value['product_id']
                product = http.request.env['wishlist'].sudo().search(['&',('partner_id.id','=',user.partner_id.id),('product_id.id','=',product_id)])
                if product:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Product Already in Wishlist"}),headers=headers)     
                else:
                    http.request.env['wishlist'].with_user(user.id).create({
                        'partner_id':user.partner_id.id,
                        'product_id':product_id
                    }) 
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Added to Wishlist!"}}),headers=headers)     
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)     

    ### View Wishlist
    @http.route('/api/viewWishlist', auth='none',type='http',csrf=False,website=False,methods=['GET'])
    def view_wishlist(self):
        headers = {'content-type':'application/json'}
        try:
            if(http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                wishlist = http.request.env['wishlist'].sudo().search([('partner_id.id','=',user.partner_id.id)])
                products = []
                digit_set = set()
                status = False
                for w in wishlist:
                    product = http.request.env['product.template'].sudo().search([("id",'=',w.product_id.id)])
                    for p in product:
                        digits = ''.join(filter(str.isdigit, str(p['image_1920'].decode())))
                        unique_digits = ''.join(set(digits))
                        unique_digits = unique_digits[:5]
                        image_hash = hashlib.md5(p['image_1920']).hexdigest()
                        if (unique_digits, image_hash) not in digit_set:
                            digit_set.add((unique_digits, image_hash))
                            url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (p.id,  image_hash)
                            url += '?%s' % unique_digits
                        if p.qty_available <=0:
                            status = False
                        else:
                            status = True
                        products.append({
                            "id":p.id,
                            "name":p.name,
                            'is_vip':p.vip,
                            'is_on_sale':p.sale,
                            'regular_price':p.list_price,
                            'new_price':p.vip_price if p.vip == True else p.sale_price if p.sale == True else 0.0,
                            'category':p.categ_id.name,
                            'in_stock':status,
                            'image':url
                        })
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":products}),headers=headers)     
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers) 
            
    ### Add to wishlist
    @http.route('/api/removeFromWishlist', auth='none',type='http',csrf=False,website=False,methods=['POST','DELETE'])
    def delete_from_wishlist(self,**kw):
        headers = {'Content-Type':'application/json'}
        try:
            if(http.request.session.uid != None):
                product_id = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    product_id = value['product_id']
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                http.request.env['wishlist'].sudo().search(['&',('partner_id.id',"=",user.partner_id.id),('product_id.id','=',product_id)]).unlink()
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Removed from Wishllist"}}),headers=headers)     
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)   
        
    #### Home Page
    @http.route('/api/homepage',auth="public",type="http",csrf=False,methods=["GET"])
    def home_page(self):
        headers = {'Content-Type':"application/json"}
        try:
            banner = http.request.env['banners'].sudo().search([])
            banners = []
            digit_set5 = set()
            if banner:
               for b in banner:
                    for i in range(1, 6):
                        image_name = 'image_%s' % i
                        if getattr(b, image_name):
                            # get the first 5 unique digits from the binary image
                            digits = ''.join(filter(str.isdigit, str(b[image_name].decode())))
                            unique_digits = ''.join(set(digits))
                            unique_digits = unique_digits[:5]
                            image_hash = hashlib.md5(b[image_name]).hexdigest()
                            # append the digits and hash to the URL only if they are unique
                            if (unique_digits, image_hash) not in digit_set5:
                                digit_set5.add((unique_digits, image_hash))
                                url = 'https://quico-odoo.net/web/image/banners/%s/%s/%s' % (b.id, image_name, image_hash)
                                url += '?%s' % unique_digits
                                banners.append(url)
                                # break out of the loop if we have collected 5 unique images
                                if len(banners) == 5:
                                    break
                    # break out of the outer loop if we have collected 5 unique images
                    if len(banners) == 5:
                        break
            service = http.request.env['fsm.tag'].sudo().search([],order="priority asc")
            services= []
            digit_set4 = set()
            for serv in service:
                if (serv.icon):
                    digits = ''.join(filter(str.isdigit, str(serv['icon'].decode())))
                    unique_digits = ''.join(set(digits))
                    unique_digits = unique_digits[:5]
                    image_hash = hashlib.md5(serv['icon']).hexdigest()
                    if (unique_digits, image_hash) not in digit_set4:
                        digit_set4.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/fsm.tag/%s/icon/%s' % (serv.id,  image_hash)
                        url += '?%s' % unique_digits
                services.append({
                    "id":serv.id,
                    "name":serv.name,
                    "priority":serv.priority,
                    "have_service_type":serv.have_service_type,
                    "image":url if url else ""
                })
            categories = []
            top_level_categories = http.request.env['product.category'].sudo().search(['&',('parent_id', '=', False),('id','!=',1),('id','!=',89)], order='priority asc')
            digit_set3 = set()
            category_data={}
            subcategories = None
            for category in top_level_categories:
                if (category.image):
                    digits = ''.join(filter(str.isdigit, str(category['image'].decode())))
                    unique_digits = ''.join(set(digits))
                    unique_digits = unique_digits[:5]
                    image_hash = hashlib.md5(category['image']).hexdigest()
                    if (unique_digits, image_hash) not in digit_set4:
                        digit_set3.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.category/%s/image/%s' % (category.id,  image_hash)
                        url += '?%s' % unique_digits
                if category.product_count != 0:
                    category_data = {
                        'id': category.id,
                        'name': category.name,
                        "image":url if url else "",
                        'subcategories': []
                    }
                    categories.append(category_data)
                subcategories = http.request.env['product.category'].sudo().search([('parent_id.id', '=', category.id)])
                subcategory_list = []  # Create a separate list for subcategories
                for subcategory in subcategories:
                        subcategory_list.append({
                            'id': subcategory.id,
                            'name': subcategory.name
                        })
    # Append the subcategory list to the 'subcategories' key of category_data
                category_data['subcategories'] = subcategory_list
                subcategory_list.insert(0, {'id': 1, 'name': 'All'})
            vip = http.request.env['product.template'].sudo().search(['&',("vip","=",True),('detailed_type', '=', 'product')],limit=10)
            vip_products = []
            for v in vip:
                vip_products.append({
                    "id":v.id,
                    "name":v.name,
                    'category':v.categ_id.name,
                    'is_vip':v.vip,
                    'regular_price':v.list_price,
                    'new_price':v.vip_price if v.vip == True else v.sale_price if v.sale == True else 0.0,
                    "image":('https://quico-odoo.net/web/image/product.template/%s/image_1920' % v.id) if (v.image_1920) else ""
                }) 
            brand = http.request.env['product.attribute'].sudo().search([('name','=',"BRAND")])
            brands = []
            digit_set2 = set()
            for brand in brand:
                brand_values = http.request.env['product.attribute.value'].sudo().search([('attribute_id.id','=',brand.id)],limit=15)
                for b in brand_values:
                    # check if the brand has products associated with it
                    product_templates = http.request.env['product.template.attribute.value'].sudo().search([('attribute_id','=',brand.id),('product_attribute_value_id','=',b.id)])
                    if product_templates:
                        if (b.image):
                            digits = ''.join(filter(str.isdigit, str((b.image).decode())))
                            unique_digits = ''.join(set(digits))[:5]
                            image_hash = hashlib.md5((b.image)).hexdigest()
                            if (unique_digits, image_hash) not in digit_set2:
                                digit_set2.add((unique_digits, image_hash))
                                url = 'https://quico-odoo.net/web/image/product.attribute.value/%s/image/%s' % (b.id,  image_hash)
                                url += '?%s' % unique_digits
                        brands.append({
                            "id":b.id,
                            "name":b.name,
                            "image":url
                        })
            bundles = []
            challenges = []
            hot_deal = http.request.env['product.template'].sudo().search(['&',("hot_deal","=",True),("detailed_type","=","product"),('product_priority',"!=","0")],limit=10,order="product_priority asc")
            hot_deals = []
            digit_set=set()
            for h in hot_deal:
                    digits = ''.join(filter(str.isdigit, str(h['image_1920'].decode())))
                    unique_digits = ''.join(set(digits))
                    unique_digits = unique_digits[:5]
                    image_hash = hashlib.md5(h['image_1920']).hexdigest()
                    if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (h.id,  image_hash)
                        url += '?%s' % unique_digits
                    hot_deals.append({
                    "id":h.id,
                    "name":h.name,
                    'category':h.categ_id.name,
                    'is_on_sale':h.sale,
                    'regular_price':h.list_price,
                    "product_priority":int(h.product_priority) if h.product_priority else 0,
                    'new_price':h.vip_price if h.vip == True else h.sale_price if h.sale == True else 0.0,
                    "image":url
                })
            #best_sell = http.request.env['sale.order.line'].sudo().search([('product_id.product_tmpl_id.detailed_type','ilike','product')]) 
            #best_sellers = []
            #for product in best_sell:
                #best_sellers.append({
                    #'id':product.product_id.product_tmpl_id.id,
                    #'name':product.product_id.product_tmpl_id.name,
                    #'is_vip':product.product_id.product_tmpl_id.vip,
                    #'is_on_sale':product.product_id.product_tmpl_id.sale,
                    #'regular_price':product.product_id.product_tmpl_id.list_price,
                    #'new_price':product.product_id.product_tmpl_id.vip_price if product.product_id.product_tmpl_id.vip == True else product.product_id.product_tmpl_id.sale_price if product.product_id.product_tmpl_id.sale == True else 0.0,
                    #'category':product.product_id.product_tmpl_id.categ_id.name,
                    #'image':('http://35.180.100.195:8069/web/image/product.template/%s/image_1920' % product.product_id.product_tmpl_id.id) if product.product_id.product_tmpl_id.image_1920 != False else ""
                #})
            #ids = []
            #sorted_ids = []
            #for i in best_sellers:
                #ids.append(i['id'])
            #my_dict = {item: ids.count(item) for item in ids}
            #for key, value in sorted(my_dict.items(), key=lambda kv: kv[1], reverse=True):
                #sorted_ids.append(key)
            #products_filtered = sorted(best_sellers, key= lambda x: sorted_ids.index(x['id']))
            #unique_products = list({ each['id'] : each for each in products_filtered}.values()) 
            #sorted_products = []
            #for i in unique_products[:15]:
                #sorted_products.append(i)
            offer = http.request.env['product.template'].sudo().search(['&',("offer","=",True),("detailed_type","=","product")],limit=10,order="priority asc")
            offers = []
            digit_set1 = set()
            for o in offer:
                if (o.image_1920):
                    digits = ''.join(filter(str.isdigit, str(o['image_1920'].decode())))
                    unique_digits = ''.join(set(digits))
                    unique_digits = unique_digits[:5]
                    image_hash = hashlib.md5(o['image_1920']).hexdigest()
                    if (unique_digits, image_hash) not in digit_set1:
                        digit_set1.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (o.id,  image_hash)
                        url += '?%s' % unique_digits
                offers.append({
                    "id":o.id,
                    "name":o.name,
                    'category':o.categ_id.name,
                    'is_on_sale':o.sale,
                    'regular_price':o.list_price,
                    'priority':int(o.priority) if o.priority else 0,
                    'new_price':o.vip_price if o.vip == True else o.sale_price if o.sale == True else 0.0,
                    "image":url
                }) 
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"banners":banners,"services":services,"categories":categories,"vip_products":vip_products,"brands":brands,"bundles":bundles,"challenges":challenges,"hot_deals":hot_deals,"offers":offers}}),headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers)

    ### Hot Deals   
    @http.route('/api/hotDeals',auth="public",type="http",csrf=False,methods=["POST"])
    def hot_deals (self,**kw):
        try:
            products_list = []
            product_name = ""
            page_number = 0
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                    page_number = value['page']
                    if (value.get("name")):
                        product_name = value.get("name")
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("hot_deal","=",True),('detailed_type', '=', 'product')],limit=per_page,offset=offset)
            total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("hot_deal","=",True),('detailed_type', '=', 'product')])
            total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            pagination ={}
            digit_set = set()
            for product in products:
                brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])
                digits = ''.join(filter(str.isdigit, str(product['image_1920'].decode())))
                unique_digits = ''.join(set(digits))
                unique_digits = unique_digits[:5]
                image_hash = hashlib.md5(product['image_1920']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                        url += '?%s' % unique_digits
                products_list.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_values.name if brand_values else "",
                    'image':url
                })
            pagination = {
                "page":page_number if page_number > 0 else 1,
                "size":0 if len(products_list) == [] else len(products_list),
                "total_pages":total_pages
            }
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,"result":{"products":products_list,"pagination":pagination}}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':str(e)}),headers={'content-type':'application/json'})

    ### Offers
    @http.route('/api/offers',auth="public",type="http",csrf=False,methods=["POST"])
    def offers (self,**kw):
        try:
            products_list = []
            product_name = ""
            page_number = 0
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                    page_number = value['page']
                    if (value.get("name")):
                        product_name = value.get("name")
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("offer","=",True),('detailed_type', '=', 'product')],limit=per_page,offset=offset)
            total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("offer","=",True),('detailed_type', '=', 'product')])
            total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            pagination ={}
            digit_set = set()
            for product in products:
                brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])
                digits = ''.join(filter(str.isdigit, str(product['image_1920'].decode())))
                unique_digits = ''.join(set(digits))
                unique_digits = unique_digits[:5]
                image_hash = hashlib.md5(product['image_1920']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                        url += '?%s' % unique_digits
                products_list.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_values.name if brand_values else "",
                    'image':url
                })
            pagination = {
                "page":page_number if page_number > 0 else 1,
                "size":0 if len(products_list) == [] else len(products_list),
                "total_pages":total_pages
            }
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,"result":{"products":products_list,"pagination":pagination}}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':str(e)}),headers={'content-type':'application/json'})

    ### VIP
    @http.route('/api/vip',auth="public",type="http",csrf=False,methods=["POST"])
    def vip (self,**kw):
        try:
            products_list = []
            product_name = ""
            page_number = 0
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                    page_number = value['page']
                    if (value.get("name")):
                        product_name = value.get("name")
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("vip","=",True),('detailed_type', '=', 'product')],limit=per_page,offset=offset)
            total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("vip","=",True),('detailed_type', '=', 'product')])
            total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            pagination ={}
            digit_set = set()
            for product in products:
                brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])
                products_list.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_values.name if brand_values else "",
                    'image':('https://quico-odoo.net/web/image/product.template/%s/image_1920' % product.id) if product.image_1920 != False else ""
                })
            pagination = {
                "page":page_number if page_number > 0 else 1,
                "size":0 if len(products_list) == [] else len(products_list),
                "total_pages":total_pages
            }
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,"result":{"products":products_list,"pagination":pagination}}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':str(e)}),headers={'content-type':'application/json'})

    ### best
    @http.route('/api/bestSelling',auth="public",type="http",csrf=False,methods=["GET"])
    def best_selling (self,**kw):
        try:
            best_sell = http.request.env['sale.order.line'].sudo().search([('product_id.product_tmpl_id.detailed_type','ilike','product')]) 
            best_sellers = []
            for product in best_sell:
                best_sellers.append({
                    'id':product.product_id.product_tmpl_id.id,
                    'name':product.product_id.product_tmpl_id.name,
                    'is_vip':product.product_id.product_tmpl_id.vip,
                    'is_on_sale':product.product_id.product_tmpl_id.sale,
                    'regular_price':product.product_id.product_tmpl_id.list_price,
                    'new_price':product.product_id.product_tmpl_id.vip_price if product.product_id.product_tmpl_id.vip == True else product.product_id.product_tmpl_id.sale_price if product.product_id.product_tmpl_id.sale == True else 0.0,
                    'category':product.product_id.product_tmpl_id.categ_id.name,
                    'image':('https://quico-odoo.net/web/image/product.template/%s/image_1920' % product.product_id.product_tmpl_id.id) if product.product_id.product_tmpl_id.image_1920 != False else ""
                })
            ids = []
            sorted_ids = []
            for i in best_sellers:
                ids.append(i['id'])
            my_dict = {item: ids.count(item) for item in ids}
            for key, value in sorted(my_dict.items(), key=lambda kv: kv[1], reverse=True):
                sorted_ids.append(key)
            products_filtered = sorted(best_sellers, key= lambda x: sorted_ids.index(x['id']))
            unique_products = list({ each['id'] : each for each in products_filtered}.values()) 
            sorted_products = []
            for i in unique_products[:15]:
                sorted_products.append(i)
            if sorted_products:
                return http.Response(json.dumps({'jsonrpc':'2.0','id':None,"result":sorted_products}),headers = {'content-type':'application/json'})
            else:
                return http.Response(json.dumps({'jsonrpc':'2.0','id':None,"result":[]}),headers = {'content-type':'application/json'})
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc':'2.0','id':None,'error':str(e)}),headers={'content-type':'application/json'})

    ### Search Products
    @http.route('/api/searchCompare', auth='public', type='http', csrf=False, methods=['POST'])
    def search_compare(self, **kw):
        try:
            product_name = ""
            json_object = json.loads(http.request.httprequest.data)
            for key, value in json_object.items():
                product_name = value['name']
            products = http.request.env['product.template'].sudo().search(
                ['&', ("name".lower(), 'ilike', product_name.lower()), ("detailed_type", '=', "product")], limit=80)
            product_details = []
            digit_set = set()
            image_url_template = 'https://quico-odoo.net/web/image/product.template/{id}/image_1920/{image_hash}?{unique_digits}'
            url_cache = {}

            for product in products:
                if product['image_1920']:
                    image_hash = hashlib.md5(product['image_1920']).hexdigest()
                    digits = ''.join(filter(str.isdigit, image_hash))
                    unique_digits = ''.join(set(digits))[:5]
                    cache_key = (unique_digits, image_hash)

                    if cache_key in url_cache:
                        url = url_cache[cache_key]
                    else:
                        url = image_url_template.format(id=product.id, image_hash=image_hash, unique_digits=unique_digits)
                        url_cache[cache_key] = url

                    product_details.append({
                        'id': product.id,
                        'name': product.name,
                        'is_vip': product.vip,
                        'is_on_sale': product.sale,
                        'regular_price': product.list_price,
                        'new_price': product.vip_price if product.vip else product.sale_price if product.sale else 0.0,
                        'category': product.categ_id.name,
                        "image": url
                    })
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": product_details}),
                                headers={'content-type': 'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": str(e)}),
                                headers={'content-type': 'application/json'})
    
    ### subscribe to vip 
    @http.route('/api/subscribe', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def subscribe_to_vip(self,**kw):
        try:
            if (http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id',"=",http.request.session.uid)])
                product_with_vip = http.request.env['cart'].sudo().search(['&',('partner_id.id','=',user.partner_id.id),("product_id.name",'ilike',"vip charge")])
                vip_charge = http.request.env['product.template'].sudo().search([('name','ilike','vip charge')])
                if user.partner_id.is_vip != True:
                    if product_with_vip:
                        return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Subscription Charge Already in Cart "}), headers={'content-type':'application/json'})
                    else:
                        partner = http.request.env['res.partner'].sudo().search([('parent_id.id','=',user.partner_id.id)]).ids
                        orders = http.request.env['stock.picking'].sudo().search(["&",('state','!=','cancel'),"|",("partner_id.id",'=',user.partner_id.id),('partner_id.id','in',partner)]) 
                        canceled_orders = http.request.env['stock.picking'].sudo().search(["&",('state','ilike','cancel'),"|",("partner_id.id",'=',user.partner_id.id),('partner_id.id','in',partner)]) 
                        can_add_vip = False
                        products = []
                        print (canceled_orders)
                        print(orders)
                        if canceled_orders and not orders:
                                can_add_vip = True
                        elif not canceled_orders and orders:
                            for o in orders:
                                order_line = http.request.env['sale.order.line'].sudo().search([('order_id.name','=',o.origin)])
                                for ol in order_line:
                                    products.append(ol.name)
                                    if "vip charge" in products:
                                        can_add_vip = False
                                    else:
                                        can_add_vip = True
                        elif canceled_orders and orders:
                            for o in orders:
                                order_line = http.request.env['sale.order.line'].sudo().search([('order_id.name','=',o.origin)])
                                for ol in order_line:
                                    products.append(ol.name)
                                    if "vip charge" in products:
                                        can_add_vip = False
                                    else:
                                        can_add_vip = True
                        else:
                                can_add_vip = True
                        print (products)    
                        print (can_add_vip)
                        if (can_add_vip == True):
                            http.request.env['cart'].with_user(user.id).create({
                                    'partner_id': user.partner_id.id,
                                    'product_id': vip_charge.id,
                                    "quantity":1,
                                })
                        else:
                            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Sorry, You cant add VIP Charge right now"}), headers={'content-type':'application/json'})
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Successfully Added Subscription Charge to Cart"}}), headers={'content-type':'application/json'})
                else:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Sorry, You are already a VIP member"}), headers={'content-type':'application/json'})
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}), headers={'content-type':'application/json'})
        except Exception as e:
                 return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers={'content-type':'application/json'})

    ### Get Filter Options
    @http.route('/api/getFilterOptions', auth='public',type='http',csrf=False,methods=['GET'])
    def get_filter_options(self,**kw):
        try:
            categories = []
            brands = []
            brand = http.request.env['product.attribute'].sudo().search([('name','=',"BRAND")])
            for brand in brand:
                brand_values = http.request.env['product.attribute.value'].sudo().search([('attribute_id.id','=',brand.id)])
                for b in brand_values:
                    brands.append({
                        "id":b.id,
                        "name":b.name,
                    })
            category = http.request.env['product.category'].sudo().search([('parent_id.id',"!=",1)])
            categories = []
            for cat in category:
                if cat.parent_id.id != False:
                    categories.append({
                        "id":cat.id,
                        "name":cat.name,
                    })
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"categories":categories,"brands":brands}}),headers = {'content-type':'application/json'}) 
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'}) 

    ### Filter
    @http.route('/api/filter', auth='public',type='http',csrf=False,methods=['POST'])
    def filter(self,**kw):
        try:
            brand = None
            category = None
            max = 0
            condition = ""
            page_number = 0
            product_name = ""
            json_objectt = json.loads(http.request.httprequest.data)
            for key,value in json_objectt.items():
                page_number = value['page']
                if(value.get('category_id')):
                    category = value.get('category_id')
                if(value.get('brand_id')):
                    brand = value.get('brand_id')
                if(value.get('max_price')):
                    max = value.get('max_price')
                if(value.get('condition')):
                    condition = value.get('condition')    
                if(value.get('name')):
                    product_name = value.get('name')
            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            brand_values = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_attribute_value_id.id','=',brand),('attribute_id.name','=',"BRAND")])
            brands = []
            for b in brand_values:
                brands.append(b.product_tmpl_id.id)
            conditions = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_attribute_value_id.name','ilike',condition),('attribute_id.name','=',"Condition")])
            conditionss = []
            for c in conditions:
                conditionss.append(c.product_tmpl_id.id)
            if (brand == None and category == None and condition == ""):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product")])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            elif (category != None and brand == None and condition == ""):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("categ_id.id",'=',category)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("categ_id.id",'=',category)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            elif(brand != None and condition == "" and category == None ):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("id","in",brands)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("id","in",brands)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            elif(condition != "" and brand == None and category == None):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("id","in",conditionss)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("id","in",conditionss)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            elif(condition != "" and brand != None and category == None):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("id","in",brands),("id","in",conditionss)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("id","in",brands),("id","in",conditionss)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            elif(condition == "" and brand != None and category != None):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("categ_id.id","=",category),("id","in",brands)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("categ_id.id","=",category),("id","in",brands)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page) 
            elif(condition != "" and brand == None and category != None):
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("categ_id.id","=",category),("id","in",conditionss)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("categ_id.id","=",category),("id","in",conditionss)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            else:
                products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),("detailed_type","=","product"),('list_price','<=',max),("categ_id.id","=",category),("id","in",brands),("id","in",conditionss)],limit=per_page,offset=offset)
                total_products = http.request.env['product.template'].sudo().search(['&',("name".lower(),'ilike',product_name.lower()),('list_price','<=',max),("detailed_type","=","product"),("categ_id.id","=",category),("id","in",brands),("id","in",conditionss)])
                total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page)
            product_details = []
            digit_set = set()
            for product in products:
                brand_value = http.request.env['product.template.attribute.value'].sudo().search(['&',('product_tmpl_id.id','=',product.id),('attribute_id.name','=',"BRAND")])
                digits = ''.join(filter(str.isdigit, str(product['image_1920'].decode())))
                unique_digits = ''.join(set(digits))
                unique_digits = unique_digits[:5]
                image_hash = hashlib.md5(product['image_1920']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id,  image_hash)
                        url += '?%s' % unique_digits
                product_details.append({
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'brand':brand_value.name if brand_value else "",
                    "image":url
                })
            pagination = {
                "page":page_number if page_number > 0 else 1,
                "size":0 if len(product_details) == [] else len(product_details),
                "total_pages":total_pages
            }
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"products":product_details,"pagination":pagination}}),headers = {'content-type':'application/json'}) 
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers = {'content-type':'application/json'}) 

    ### check Vip Expire
    @http.route('/api/checkVip', auth='none',type='http',csrf=False,website=False,methods=['GET'])
    def check_vip(self):
        headers = {'content-type':'application/json'}
        try:
            if(http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                vip = http.request.env['vip.subscribe'].sudo().search([("subscriber_id.id",'=',user.partner_id.id)])
                if vip:
                    for v in vip:
                        if v.end_date < datetime.date.today():
                            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"is_vip":False}}),headers=headers)     
                        else:
                            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"is_vip":True}}),headers=headers)     
                else:
                    return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"is_vip":False}}),headers=headers)     
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers) 

    ### Vip Details
    @http.route('/api/vipInfo', auth='none',type='http',csrf=False,website=False,methods=['GET'])
    def vip_info(self):
        headers = {'content-type':'application/json'}
        try:
            if(http.request.session.uid != None):
                user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                vip = http.request.env['vip.subscribe'].sudo().search([("subscriber_id.id",'=',user.partner_id.id)])
                subscriber = {}
                for s in vip:
                    subscriber = {
                        "subscription_date":str(s.start_date.strftime("%d-%m-%Y")),
                        "expiration_date":str(s.end_date.strftime("%d-%m-%Y")),
                        "cost":int(s.cost)
                    }
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":subscriber}),headers=headers)                     
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Session expired"}),headers=headers)     
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers=headers) 




    ### Product
    @http.route('/api/getProductss', auth='public', type="http", csrf=False, methods=['GET'])
    def get_productss(self, **kwargs):
        try:
            page_number = int(kwargs.get('page', 1))
            per_page = int(kwargs.get('limit', 15))
            name = kwargs.get('name')
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page
            product_details = []
            digit_set = set()
            products = http.request.env['product.template'].sudo().search(['&',('detailed_type','=','product'),('name','ilike',name)], offset=offset, limit=per_page)
            total_products = http.request.env['product.template'].sudo().search([('detailed_type','=','product')])
            total_pages = 1 if math.ceil(len(total_products)/per_page) <= 1 else math.ceil(len(total_products)/per_page) 
            total = 0
            for product in products:
                if product['image_1920']:
                    digits = ''.join(filter(str.isdigit, str(product['image_1920'].decode())))
                    unique_digits = ''.join(set(digits))
                    unique_digits = unique_digits[:5]
                    image_hash = hashlib.md5(product['image_1920']).hexdigest()
                if (unique_digits, image_hash) not in digit_set:
                    digit_set.add((unique_digits, image_hash))
                    url = 'https://quico-odoo.net/web/image/product.template/%s/image_1920/%s' % (product.id, image_hash)
                    url += '?%s' % unique_digits
                product_details.append({
                    'id': product.id,
                    'name': product.name,
                    'is_vip': product.vip,
                    'is_on_sale': product.sale,
                    'regular_price': product.list_price,
                    'new_price': product.vip_price if product.vip else product.sale_price if product.sale else 0.0,
                    'category': product.categ_id.name,
                    'image': url
                })
            for p in total_products:
                total = total + 1
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": product_details,"total_pages":total}), headers={'content-type': 'application/json'})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": str(e)}), headers={'content-type': 'application/json'})

    ### Get Product By id (single page)
    @http.route('/api/getProductt', auth='none',type='http',csrf=False,methods=['GET'])
    def get_products_by_idd(self,**kwargs):
        headers = {'Content-Type': 'application/json'}
        try:
            id = kwargs.get('id')
            products = http.request.env['product.template'].sudo().search([("id",'=',id)])
            product_details = {}
            status = None
            wishlist =  None
            cart = None
            imagess = []
            digit_set = set()
            if (http.request.session.uid != None):
                    user = http.request.env['res.users'].sudo().search([('id','=',http.request.session.uid)])
                    wishlist = http.request.env['wishlist'].sudo().search([('product_id.id','=',id)])
                    cart = http.request.env['cart'].sudo().search(['&',('product_id.id','=',id),('partner_id.id','=',user.partner_id.id)])
            for product in products:
                attributes = http.request.env['product.template.attribute.value'].sudo().search([('product_tmpl_id.id','=',product.id)])
                images = http.request.env['product.image'].sudo().search([('product_tmpl_id.id','=',product.id)])
                for img in images:
                    if (img.image_1920):
                        digits = ''.join(filter(str.isdigit, str((img.image_1920).decode())))
                        unique_digits = ''.join(set(digits))[:5]
                        image_hash = hashlib.md5((img.image_1920)).hexdigest()
                        if (unique_digits, image_hash) not in digit_set:
                            digit_set.add((unique_digits, image_hash))
                            url = 'https://quico-odoo.net/web/image/product.image/%s/image_1920/%s' % (img.id,  image_hash)
                            url += '?%s' % unique_digits
                            imagess.append(url)
                if product.qty_available <= 0:
                    status = False
                else:
                    status = True
                product_details={
                    'id':product.id,
                    'name':product.name,
                    'is_vip':product.vip,
                    'is_on_sale':product.sale,
                    'is_in_wishlist':True if wishlist else False,
                    'is_vip_charge_product':True if product.name == "vip charge" else False,
                    'regular_price':product.list_price,
                    'new_price':product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                    'category':product.categ_id.name,
                    'quantity':cart.quantity if cart else 0,
                    'quantity_available':int(product.qty_available),
                    'in_stock':status,
                    'description':product.description_sale if product.description_sale else "",
                    "specifications":[{"name":att.attribute_id.name,"value":att.name} for att in attributes],
                    'images':imagess
                }
            print(wishlist)
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":product_details}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}), headers=headers)
    

    ### delete user
    @http.route('/api/deleteUser', auth='none', type="http", csrf=False, methods=['POST', 'DELETE'])
    def delete_user(self, **kw):
        # Get user_id from request
        user_id = 0
        json_objectt = json.loads(http.request.httprequest.data)
        for key, value in json_objectt.items():
            user_id = value.get('user_id')
        if user_id == 0:
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "User ID is required"}),
                                 headers={'content-type': 'application/json'})

        ## Search for the user
        user = http.request.env['res.users'].sudo().search([('id', '=', user_id)])
        if not user:
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "User not found"}),
                                 headers={'content-type': 'application/json'})
        parent = http.request.env['res.partner'].sudo().search([('parent_id.id','=',user.partner_id.id)])
        partner = http.request.env['res.partner'].sudo().search([('id','=',user.partner_id.id)])
        pp = []
        pp.append(partner.id)
        for p in parent:
            pp.append(p.id)
        print (pp)
        # Search for sales orders related to the user
        sale_orders = http.request.env['sale.order'].sudo().search([('partner_id','in',pp)])
        service_orders = http.request.env['fsm.order'].sudo().search([('partner_id','in',pp)])
        print (sale_orders)
        deleted = False
        value = ''
        states = []
        stages = []
        if (sale_orders or service_orders) :
            for s in sale_orders:
                sp = http.request.env['stock.picking'].sudo().search([('origin','=',s.name)])
                states = ['done','cancel']
                if (s.state not in states):
                    if (sp):
                        if (sp.state not in states):
                            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "Cant Delete Account Since There is Order not Completed or not Cancelled"}),headers={'content-type': 'application/json'})
                        else:
                            deleted = True
                    else:
                        if (s.state in states):
                            deleted = True
                        else:
                            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "Cant Delete Account Since There is Order not Completed or not Cancelled"}),headers={'content-type': 'application/json'})
                else:
                    deleted = True
            for so in service_orders:
                stages = [2,3]
                if (so.stage_id.id not in stages):
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "Cant Delete Account Since There is Order not Completed or not Cancelled"}),headers={'content-type': 'application/json'})
                else:
                    deleted = True
            if deleted == True:
                for s in sale_orders:
                    s.write({'partner_id': 277,'partner_invoice_id':277,'partner_shipping_id':277})
                for so in service_orders:
                    so.write({'partner_id': 277})
                if (http.request.session.uid != None):
                    http.request.session.logout()
                # Delete the user's account
                user.unlink()
                # Unlink the user's partner (customer) record
                http.request.env['res.partner'].sudo().search([('id','in',pp)]).unlink()

        else:
            for s in sale_orders:
                s.write({'partner_id': 277,'partner_invoice_id':277,'partner_shipping_id':277})
            for so in service_orders:
                so.write({'partner_id': 277})
            if (http.request.session.uid != None):
                http.request.session.logout()
            # Delete the user's account
            user.unlink()
            # Unlink the user's partner (customer) record
            http.request.env['res.partner'].sudo().search([('id','in',pp)]).unlink()


        return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result":{'status' :"Successfully Deleted Account"}}),
                             headers={'content-type': 'application/json'})


    @http.route('/api/categoriesMenu',auth='public',type='http',csrf=False,methods=['GET'])
    def get_Categoriess(self):
        headers = {'Content-Type': 'application/json'}
        try:
            categories = []
            top_level_categories = http.request.env['product.category'].sudo().search([('parent_id', '=', False), ('product_count', '!=', 0)], order='priority asc')
            for category in top_level_categories:
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'image': ('data:image/png;base64,'+(category.image).decode('UTF-8')) if category.image else "",
                    'subcategories': []
                }
                subcategories = http.request.env['product.category'].sudo().search([('parent_id', '=', category.id), ('product_count', '!=', 0)], order='priority asc')
                for subcategory in subcategories:
                    subcategory_data = {
                        'id': subcategory.id,
                        'name': subcategory.name,
                        'image': ('data:image/png;base64,'+(subcategory.image).decode('UTF-8')) if subcategory.image else ""
                    }
                    category_data['subcategories'].append(subcategory_data)
                categories.append(category_data)
            return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'result': categories}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'result': {'error': str(e)}}), headers=headers)
   
    @http.route('/api/filterMulti', auth='public', type='http', csrf=False, methods=['POST'])
    def filterr(self, **kw):
        try:
            brand_ids = []
            category_ids = []
            max_price = 0
            condition = ""
            page_number = 0
            product_name = ""

            json_object = json.loads(http.request.httprequest.data)
            for key, value in json_object.items():
                page_number = value['page']
                if 'category_ids' in value:
                    category_ids = value.get('category_ids')
                if 'brand_ids' in value:
                    brand_ids = value.get('brand_ids')
                if 'max_price' in value:
                    max_price = value.get('max_price')
                if 'condition' in value:
                    condition = value.get('condition')
                if 'name' in value:
                    product_name = value.get('name')

            per_page = 15
            offset = 0 if page_number <= 1 else (page_number - 1) * per_page

            domain = [('name', 'ilike', product_name.lower()), ('detailed_type', '=', 'product')]
            if max_price > 0:
                domain.append(('list_price', '<=', max_price))
            if category_ids:
                domain.append(('categ_id.id', 'in', category_ids))
            if brand_ids:
                brand_values = http.request.env['product.template.attribute.value'].sudo().search(
                    ['&', ('product_attribute_value_id.id', 'in', brand_ids), ('attribute_id.name', '=', "BRAND")])
                brands = []
                for b in brand_values:
                    brands.append(b.product_tmpl_id.id)
                domain.append(('id', 'in', brands))
            if condition:
                conditions = http.request.env['product.template.attribute.value'].sudo().search(
                    ['&', ('product_attribute_value_id.name', 'ilike', condition), ('attribute_id.name', '=', "Condition")])
                condition_ids = [c.product_tmpl_id.id for c in conditions]
                if condition_ids:
                    domain.append(('id', 'in', condition_ids))

            products = http.request.env['product.template'].sudo().search(domain, limit=per_page, offset=offset)
            total_products = http.request.env['product.template'].sudo().search(domain)
            total_pages = 1 if math.ceil(len(total_products) / per_page) <= 1 else math.ceil(len(total_products) / per_page)

            product_details = []
            digit_set = set()
            image_url_template = 'https://quico-odoo.net/web/image/product.template/{id}/image_1920/{image_hash}?{unique_digits}'

            for product in products:
                if product.image_1920:
                    digits = ''.join(filter(str.isdigit, str(product.image_1920.decode())))
                    unique_digits = ''.join(set(digits))
                    unique_digits = unique_digits[:5]
                    image_hash = hashlib.md5(product.image_1920).hexdigest()
                    if (unique_digits, image_hash) not in digit_set:
                        digit_set.add((unique_digits, image_hash))
                        url = image_url_template.format(id=product.id, image_hash=image_hash, unique_digits=unique_digits)
                    else:
                        url = ""
                else:
                    url = ""

                product_details.append({
                'id': product.id,
                'name': product.name,
                'is_vip': product.vip,
                'is_on_sale': product.sale,
                'regular_price': product.list_price,
                'new_price': product.vip_price if product.vip == True else product.sale_price if product.sale == True else 0.0,
                'category': product.categ_id.name,
                'image': url
                })
    
            pagination = {
                "page": page_number if page_number > 0 else 1,
                "size": len(product_details),
                "total_pages": total_pages
            }

            response_data = {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "products": product_details,
                    "pagination": pagination
                }
            }

            return http.Response(json.dumps(response_data), headers={'content-type': 'application/json'})

        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": str(e)
            }
            return http.Response(json.dumps(error_response), headers={'content-type': 'application/json'})

    @http.route('/api/productRate',auth='none',type='http',csrf=False,methods=['POST'])
    def product_rate(self):
        try:
            if (http.request.session.uid != None):
                user_id = None
                product_id = None
                rate = None
                json_object = json.loads(http.request.httprequest.data)
                for key,value in json_object.items():
                    user_id = value['user_id']
                    product_id = value['product_id']
                    rate = value['rate']
                user_idd = http.request.env['res.users'].sudo().search([('id','=',user_id)]).partner_id
                partner_id = http.request.env['res.partner'].sudo().search([('id','=',user_idd.id)])
                new_record = http.request.env['rating.product'].sudo().create({
                    'user_id': user_id,
                    'partner_id':partner_id.id,
                    'product_id': product_id,
                    'rating': rate,
                })
                return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'result': {'status':'successfully Added Rate'}}), status=200,headers = {'Content-Type': 'application/json'})
            else:
                return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'error': 'Session Expired'}),  headers = {'Content-Type': 'application/json'})
        except Exception as e:
            return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'error': str(e)}),  headers = {'Content-Type': 'application/json'})
    
    @http.route('/api/register_login', auth='public', type='http', csrf=False, methods=['POST'])
    def register_or_login(self):
        email = None
        password = None
        json_object = json.loads(http.request.httprequest.data)
        for key,value in json_object.items():
            email = value['email']
            password = value['password']

        api_key = "AIzaSyDaoLknXHqhJY_zcKlAxV2UX0tnl0OdM5w"

        # Check if user exists
        check_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        check_data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
        }
        check_response = requests.post(check_url, json=check_data)
        if check_response.ok:
            # User exists, return success response
            return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'result': {'status':'successfully'}}))

        # User does not exist or login failed, return error response
        error_message = check_response.json().get("error", {}).get("message", "Unknown error")
        return http.Response(json.dumps({'jsonrpc': '2.0', 'id': None, 'error': 'error'}))
    
    ### Add to cart 
    @http.route('/api/checkUserExist', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def check_user_exist(self,**kw):
        headers = {'Content-Type':"application/json"}
        try:
            mobile = None
            email = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                mobile = value['mobile']
                if 'email' in value:
                    email = value['email']
            user_mob = http.request.env['res.partner'].sudo().search([('mobile','=',mobile)])
            user_email = http.request.env['res.users'].sudo().search([('login','=',email)])
            if (user_mob and user_email):
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"user_existence":True,"message":"Phone Number and Email Already Exist"}}), headers=headers)
            elif (user_email):
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"user_existence":True,"message":"Email Already Exist"}}), headers=headers)
            elif (user_mob):
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"user_existence":True,"message":"Phone Number Already Exist"}}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"user_existence":False,"message":"The Data Needed Doesn't Exist"}}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)
     
    @http.route('/api/sendOTP', auth='none', type='http', csrf=False, website=False, methods=['POST'])
    def send_otp(self, **kw):
        headers = {'Content-Type': 'application/json'}
        try:
            http_request = None
            http_request = urllib3.PoolManager()
            mobile = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                mobile = value['mobile'][1:]
            
            # Fetch the existing verify.user record (if any) for the given mobile number
            verify_user = http.request.env['verify.user'].sudo().search([('mobile', '=', mobile)])

            fixed_digits = 6
            code = random.randrange(111111, 999999, fixed_digits)

            # Your logic for making another API request using 'requests' library with X-Access-Token and basic authorization
            sms_url = "https://httpsmsc02.montymobile.com/HTTP/api/Client/SendSMS"
            sms_body = {
                "source": "Quicotech",
                "destination": mobile,
                "text": "Welcome to QuicoTech. Your verification code is: "+str(code)+". "+"Please enter this code to complete the process."
            }
            sms_headers = {
                "Username":"Quicotech",
                "Password":"I7ch3r#g",
                "content-type":"application/json"
            }
            try:
                if verify_user.counter >= 3:
                     return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result":{"code_sent":False,"message":"User Has Done 3 Attempts Try Again After 12 hours"}}), headers=headers)
                else:
                    sms_response = requests.post(sms_url, json=sms_body, headers=sms_headers)
                    if sms_response.status_code == 200:
                        # If the API request is successful, update the counter or create a new record
                        if verify_user:
                            verify_user.sudo().write({
                                "expired": False,
                                "time": datetime.datetime.now(),
                                "code": code,
                                "counter": verify_user.counter + 1  # Increment the existing counter
                            })
                        else:
                            http.request.env['verify.user'].sudo().create({
                                "expired": False,
                                "time": datetime.datetime.now(),
                                "code": code,
                                "mobile": mobile,
                                "counter": 1  # Set counter to 1 for new records
                            })
                    else:
                        return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result":{"code_sent":False,"message":"Something Went Wrong Please Try Again Later"}}), headers=headers)

            except requests.exceptions.RequestException as e:
                return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": str(e)}), headers=headers, status=500)

            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": {"code_sent":True,"message":"Message Sent Successfully"}}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": str(e)}), headers=headers, status=500)
    
    ### Add to cart 
    @http.route('/api/verifyOTP', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def verify_otp(self,**kw):
        headers = {'Content-Type':"application/json"}
        try:
            code = None
            mobile = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                code = value['code']
                mobile = value['mobile'][1:]
            user = http.request.env['verify.user'].sudo().search([('mobile','=',mobile)])
            if user.counter > 3:
                return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result":{"is_verified":False,"message":"User Has Done 3 Attempts Try Again After 12 hours"}}), headers=headers)
            else:
                if user.expired == True:
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result':{'is_verified':False,"message":'Code is Expired'}}), headers=headers)
                if user.code == code:
                    if user.counter == 3:
                        user.sudo().write({
                            'counter':user.counter + 1
                        })
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result':{'is_verified':True,"message":'Successfully Verified'}}), headers=headers)
                else:
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result':{'is_verified':False,"message":'Code is Incorrect'}}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)

    
    @http.route('/api/checkMobileFound', type='http', auth='public', methods=['POST'], csrf=False)
    def get_stations(self, **kw):
        try:
            mobile = None
            data = json.loads(http.request.httprequest.data)
            for key, value in data.items():
                mobile = value['mobile']
            phone = http.request.env['res.partner'].sudo().search([('mobile','=',mobile)])
            if (phone):
                return http.Response(json.dumps({
                    "jsonrpc":"2.0",
                    "id":None,
                    "result":{'status':'Phone Number Exist'}
                }),headers={"content-type":"application/json"})
            else:
                return http.Response(json.dumps({
                    "jsonrpc":"2.0",
                    "id":None,
                    "error":"Phone Number Doesn't exist"
                }),headers={"content-type":"application/json"})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers={"content-type":"application/json"})

    ### Add to cart
    @http.route('/api/verifyCode', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def verify_code(self,**kw):
        headers = {'Content-Type':"application/json"}
        try:
            code = None
            mobile = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                code = value['code']
                mobile = value['mobile'][1:]
            user = http.request.env['verify.user'].sudo().search([('mobile','=',mobile)])
            if user.counter > 3:
                return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'error': "You have reached the maximum number of attempts for your verification code. Please try again in 12 hours or contact our support team for assistance. Thank you for your understanding."}), headers=headers)
            else:
                if user.expired == True:
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'error': 'Code is Expired'}), headers=headers)
                if user.code == code:
                    if user.counter == 3:
                        user.sudo().write({
                            'counter': user.counter + 1
                        })
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'result':{'status': 'Verified Successfully'}}), headers=headers)
                else:
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, 'error': 'Code is Incorrect'}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)

    @http.route('/api/sendCode', auth='none', type='http', csrf=False, website=False, methods=['POST'])
    def send_mes(self, **kw):
        headers = {'Content-Type': 'application/json'}
        try:
            http_request = None
            http_request = urllib3.PoolManager()
            mobile = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                mobile = value['mobile'][1:]

            # Fetch the existing verify.user record (if any) for the given mobile number
            verify_user = http.request.env['verify.user'].sudo().search([('mobile', '=', mobile)])

            fixed_digits = 6
            code = random.randrange(111111, 999999, fixed_digits)

            # Your logic for making another API request using 'requests' library with X-Access-Token and basic authorization
            sms_url = "https://httpsmsc02.montymobile.com/HTTP/api/Client/SendSMS"
            sms_body = {
                "source": "Quicotech",
                "destination": mobile,
                "text": "Welcome to QuicoTech. Your verification code is: "+str(code)+". "+"Please enter this code to complete the process."
            }
            sms_headers = {
                "Username":"Quicotech",
                "Password":"I7ch3r#g",
                "content-type":"application/json"
            }
            try:
                if verify_user.counter >= 3:
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "You have reached the maximum number of attempts for your verification code. Please try again in 12 hours or contact our support team for assistance. Thank you for your understanding."}), headers=headers)
                sms_response = requests.post(sms_url, json=sms_body, headers=sms_headers)
                # Process the SMS API response as needed
                if sms_response.status_code == 200:
                    # If the API request is successful, update the counter or create a new record
                    if verify_user:
                        verify_user.sudo().write({
                            "expired": False,
                            "time": datetime.datetime.now(),
                            "code": code,
                            "counter": verify_user.counter + 1  # Increment the existing counter
                        })
                    else:
                        http.request.env['verify.user'].sudo().create({
                            "expired": False,
                            "time": datetime.datetime.now(),
                            "code": code,
                            "mobile": mobile,
                            "counter": 1  # Set counter to 1 for new records
                        })
                else:
                    return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": "Message Not Sent"}), headers=headers)

            except requests.exceptions.RequestException as e:
                return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": str(e)}), headers=headers, status=500)

            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "result": {'status':'Successfully Sent Message'}}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc": "2.0", "id": None, "error": str(e)}), headers=headers, status=500)


    ### Add to cart
    @http.route('/api/checkUserFound', auth='none',type='http',csrf=False,website=False,methods=['POST'])
    def check_user_found(self,**kw):
        headers = {'Content-Type':"application/json"}
        try:
            mobile = None
            email = None
            json_object = json.loads(http.request.httprequest.data)
            for key,value in json_object.items():
                mobile = value['mobile']
                email = value['email']
            user_mob = http.request.env['res.partner'].sudo().search([('mobile','=',mobile)])
            user_email = http.request.env['res.users'].sudo().search([('login','=',email)])
            if (user_mob and user_email):
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Phone Number and Email Already Exist"}), headers=headers)
            elif (user_email):
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Email Already Exist"}), headers=headers)
            elif (user_mob):
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":"Phone Number Already Exist"}), headers=headers)
            else:
                return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"result":{"status":"Success, You're Credentials are not Used Before"}}), headers=headers)
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,'error':str(e)}), headers=headers)
    
    
    @http.route('/api/getCode', type='http', auth='public', methods=['POST'], csrf=False)
    def get_code(self, **kw):
        try:
            mobile = None
            data = json.loads(http.request.httprequest.data)
            for key, value in data.items():
                mobile = value['mobile'][1:]
            code = http.request.env['verify.user'].sudo().search([('mobile','=',mobile)])
            return http.Response(json.dumps({
                "jsonrpc":"2.0",
                "id":None,
                "result":code.code
            }),headers={"content-type":"application/json"})
        except Exception as e:
            return http.Response(json.dumps({"jsonrpc":"2.0","id":None,"error":str(e)}),headers={"content-type":"application/json"})
