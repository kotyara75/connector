from marshmallow import Schema, fields, post_load, pre_dump

from connector.client import StorageSchema


class EnterpriseSchema(Schema):
    enterprise_id = fields.Integer(load_from='id', dump_to='id')


class UserSchema(Schema):
    login = fields.Email(required=True)
    name = fields.Str(required=True)
    space_amount = fields.Integer()
    role = fields.Str(load_only=True)
    admin = fields.Method('dump_role', deserialize='load_role', load_from='role', dump_to='role')
    can_see_managed_users = fields.Bool(load_only=True, default=False)
    is_sync_enabled = fields.Bool(load_only=True, default=False)
    language = fields.Str(default="en")
    job_title = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    timezone = fields.Str(default="Australia/Melbourne")
    status = fields.Str()
    user_id = fields.Str(load_only=True, load_from='id')
    enterprise = fields.Nested(EnterpriseSchema, dump_only=True)

    def dump_role(self, obj):
        return 'coadmin' if obj.admin else 'user'

    def load_role(self, role):
        return True if role == 'coadmin' else False

    @post_load
    def make_user(self, data):
        return User(**data)

    @pre_dump
    def dump_user(self, data):
        d = {k: v for k, v in data.__dict__.items() if v}
        d['enterprise'] = {'enterprise_id': data.client.enterprise_id}
        return d


class User(object):
    client = None
    login = None
    name = None
    admin = False
    can_see_managed_users = None
    space_amount = 0
    is_sync_enabled = True
    language = "en"
    job_title = None
    phone = None
    address = None
    timezone = 'Australia/Melbourne'
    status = None
    user_id = None

    def __init__(self, client=None, name=None, login=None, admin=False, space_amount=0, status=None, user_id=None,
                 phone=None, address=None, can_see_managed_users=None, is_sync_enabled=True, language='en',
                 job_title=None, timezone='Australia/Melbourne'):
        self.client = client
        self.login = login
        self.name = name
        self.admin = admin
        self.can_see_managed_users = can_see_managed_users
        self.space_amount = space_amount
        self.status = status
        if user_id:
            self.user_id = user_id
        self.phone = phone
        self.address = address
        self.is_sync_enabled = is_sync_enabled
        self.language = language
        self.job_title = job_title
        self.timezone = timezone

    def api(self):
        return self.client.reseller.api()

    def __repr__(self):
        return '<User(email={})>'.format(self.login)

    @property
    def _dump(self):
        return UserSchema().dump(self).data

    def create(self):
        api = self.api()
        result = api.users.post(self._dump)
        self.load(result)
        return result

    def update(self):
        self.api().users(self.user_id).put(self._dump)

    def refresh(self):
        api = self.api()
        result = api.users(self.user_id).get()
        self.load(result)

    def load(self, result):
        u = UserSchema().load(result).data
        self.__init__(self.client, name=u.name, login=u.login, admin=u.admin, space_amount=u.space_amount,
                status=u.status, user_id=u.user_id, phone=u.phone, address=u.address,
                can_see_managed_users=u.can_see_managed_users, is_sync_enabled=u.is_sync_enabled,
                language=u.language, job_title=u.job_title, timezone=u.timezone)

    def delete(self):
        api = self.api()
        result = api.users(self.user_id).delete()
        return result

    def token(self):
        return ''

    def login_link(self):
        return 'https://app.box.com/'
