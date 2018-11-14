# https://gist.github.com/ngse/c20058116b8044c65d3fbceda3fdf423
# Implement by using AuditableMixin in your model class declarations
# Usage:
# -----

# import lib.audit_mixin

# lib.audit_mixin.PLEASE_AUDIT = [lib.audit_mixin.ACTION_UPDATE]

# def current_user_id():
#    current_account = LoginSession.for_current_session().account
#    return current_account.id
# lib.audit_mixin._current_user_id_or_none = current_user_id

# class ImportantThing(lib.audit_mixin.AuditableMixin, Base):
#    blah blah


import datetime
import json
import logging

from reahl.sqlalchemysupport import Session, Base

from sqlalchemy import Column, Integer, String, UnicodeText, DateTime
from sqlalchemy import event, inspect
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import get_history

ACTION_CREATE = 1
ACTION_UPDATE = 2
ACTION_DELETE = 3

# Only audit the events in this list

LOGGER = logging.getLogger(__name__)

def current_user_id(): return 66666

def brute_force_dump(d):
    return json.dumps(d, indent=4, sort_keys=True, default=str)


class MyBase(Base):
    """Base model class to implement db columns and features every model should have"""

    __abstract__ = True

    id = Column(Integer, primary_key=True)


class TimestampableMixin:
    """Allow a model to track its creation and update times"""
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class AuditLog(MyBase, TimestampableMixin):
    """Model an audit log of user actions"""

    __tablename__ = 'auditlog'


    user_id = Column(Integer, doc="The ID of the user who made the change")
    target_type = Column(String(100), nullable=False, doc="The table name of the altered object")
    target_id = Column(Integer, doc="The ID of the altered object")
    action = Column(Integer, doc="Create (1), update (2), or delete (3)")
    state_before = Column(UnicodeText,
                          doc="Stores a JSON string representation of a dict containing the altered column "
                              "names and original values")
    state_after = Column(UnicodeText, doc="Stores a JSON string representation of a dict containing the altered column "
                                          "names and new values")


    def __init__(self, target_type, target_id, action, state_before, state_after):
        self.user_id = current_user_id()
        self.target_type = target_type
        self.target_id = target_id
        self.action = action
        self.state_before = state_before
        self.state_after = state_after

    def __repr__(self):
        return '<AuditLog %r: %r -> %r>' % (self.user_id, self.target_type, self.action)

    # Not in use
    def save(self, connection):
        connection.execute(
            self.__table__.insert(),
            user_id=self.user_id,
            target_type=self.target_type,
            target_id=self.target_id,
            action=self.action,
            state_before=self.state_before,
            state_after=self.state_after
        )

class AuditableMixin:
    """Allow a model to be automatically audited"""

    def create_audit(cls, connection, object_type, object_id, action, **kwargs):
        audit = AuditLog(
            object_type,
            object_id,
            action,
            kwargs.get('state_before'),
            kwargs.get('state_after')
        )
        # audit.save(connection)
        Session.add(audit)

    @classmethod
    def __declare_last__(cls):
        LOGGER.warning("DECLARE_LAST. checking {}".format(cls.audit_actions()))
        if ACTION_CREATE in cls.audit_actions():
            event.listen(cls, 'after_insert', cls.audit_insert)

        if ACTION_DELETE in cls.audit_actions():
            event.listen(cls, 'after_delete', cls.audit_delete)

        if ACTION_UPDATE in cls.audit_actions():
            event.listen(cls, 'after_update', cls.audit_update)

    @staticmethod
    def audit_insert(mapper, connection, target):
        """Listen for the `after_insert` event and create an AuditLog entry"""
        target.create_audit(connection, target.__tablename__, target.id, ACTION_CREATE)

    @staticmethod
    def audit_delete(mapper, connection, target):
        """Listen for the `after_delete` event and create an AuditLog entry"""
        target.create_audit(connection, target.__tablename__, target.id, ACTION_DELETE)

    @staticmethod
    def audit_update(mapper, connection, target):
        """Listen for the `after_update` event and create an AuditLog entry with before and after state changes"""
        LOGGER.warning("after update")
        state_before = {}
        state_after = {}
        inspr = inspect(target)
        attrs = class_mapper(target.__class__).column_attrs
        for attr in attrs:
            hist = getattr(inspr.attrs, attr.key).history
            if hist.has_changes():
                state_before[attr.key] = get_history(target, attr.key)[2].pop()
                state_after[attr.key] = getattr(target, attr.key)

        target.create_audit(connection, target.__tablename__, target.id, ACTION_UPDATE,
                            state_before=brute_force_dump(state_before),
                            state_after=brute_force_dump(state_after))

