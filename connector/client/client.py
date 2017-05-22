from marshmallow import Schema, fields, post_load, pre_dump

from connector.client import StorageSchema


class AdministeredBySchema(Schema):
    name = fields.Str(required=True)
    phone = fields.Str(allow_none=True)
    login = fields.Str(required=True)
    user_id = fields.Str(load_from='id', load_only=True)


class TrialDealField(fields.Bool):
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        elif value in self.truthy:
            return 'trial'
        elif value in self.falsy:
            return 'live_deal'

    def _deserialize(self, value, attr, data):
        return True if value == 'trial' else False


class ClientSchema(Schema):
    name = fields.Str(required=True)
    users_amount = fields.Int(load_only=True, load_from='seats_used')
    users_limit = fields.Int(load_from='seats', dump_to='seats', required=True)
    trial = TrialDealField(load_from='deal_status', dump_to='deal_status')
    trial_end_at = fields.Time(allow_none=True)
    plan_code = fields.Str(required=True, dump_only=True)
    billing_cycle = fields.Str()
    subdomain = fields.Str(allow_none=True)
    administered_by = fields.Nested(AdministeredBySchema, required=True)
    enterprise_id = fields.Str(load_from='id', load_only=True)
    active_status = fields.Str(allow_none=True)

    @post_load
    def make_client(self, data):
        return Client(**data)

    @pre_dump
    def dump_client(self, data):
        return {k: v for k, v in data.__dict__.items() if v}


class Client(object):
    reseller = None
    name = None
    users_amount = None
    users_limit = 10
    enterprise_id = None
    plan_code = None
    billing_cycle = None
    administered_by = None
    trial = None
    active_status = None

    def __init__(self, reseller=None, name=None, users_amount=None, users_limit=10,
                 trial=None, trial_end_at=None,
                 plan_code=None, billing_cycle='monthly',
                 subdomain=None, administered_by=None, enterprise_id=None, active_status = None):
        self.reseller = reseller
        self.name = name
        self.users_amount = users_amount
        self.users_limit = users_limit
        self.trial = trial
        self.trial_end_at = trial_end_at
        self.plan_code = plan_code
        self.billing_cycle = billing_cycle
        self.subdomain = subdomain
        self.administered_by = administered_by
        self.active_status = active_status
        if enterprise_id:
            self.enterprise_id = enterprise_id

    def api(self):
        return self.reseller.api()

    def __repr__(self):
        return '<Client(id={} name={})>'.format(self.enterprise_id, self.name)

    @property
    def _dump(self):
        return ClientSchema().dump(self).data

    def create(self, administered_by):
        api = self.api()
        self.administered_by = administered_by
        result = api.enterprises.post(self._dump)
        self.load(result)
        return result

    def update(self):
        return self.api().enterprises(self.enterprise_id).put(self._dump)

    def load(self, result):
        c = ClientSchema().load(result).data
        self.__init__(self.reseller, name=c.name, users_amount=c.users_amount, users_limit=c.users_limit,
                      trial=c.trial, trial_end_at=c.trial_end_at,
                      plan_code=c.plan_code, billing_cycle=c.plan_code,
                      subdomain=c.subdomain, administered_by=c.administered_by, enterprise_id=c.enterprise_id)

    def refresh(self):
        if self.enterprise_id:
            api = self.api()
            result = api.enterprises(self.enterprise_id).get()
            self.load(result)

    def delete(self):
        self.active_status = 'deactivated'
        if self.enterprise_id:
            api = self.api()
            result = api.enterprises(self.enterprise_id).put()
            return result
