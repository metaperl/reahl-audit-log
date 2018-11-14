
from datetime import datetime, timedelta
import random
import sys

from sqlalchemy import Column, Integer, UnicodeText
from datatablebootstrap import Check, Ability, account_ability, MyUI
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount
from reahl.tofu.pytestsupport import with_fixtures
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture

from reahl.sqlalchemysupport import Session, Base, metadata
from reahl.component.context import ExecutionContext
from reahl.component.config import StoredConfiguration, ReahlSystemConfig

import lib.audit_mixin


def setup():

    try:
        metadata.create_all()

    finally:
        metadata.bind = None

def init():
    ExecutionContext().install()


    config_dir = sys.argv[1]
    config = StoredConfiguration(config_dir)
    config.configure()

    db_uri = config.reahlsystem.connection_uri
    print("DB URI = {}".format(db_uri))

    metadata.bind = db_uri

    setup()

    Session.commit()


if __name__ == '__main__':
    init()
