# reahl-audit-log
Implement Audit Log for the Reahl Python-Only Web Application Frameowkr

# Usage

Place audit_mixin.py in a package directory. We will presume `lib/audit_mixin` in this case.

## in .reahlproject

In the `persisted` section add:

    <class locator="lib.audit_mixin:AuditLog"/>

## In your code

    import lib.audit_mixin

```python

def current_account():
    return LoginSession.for_current_session().account

def current_user_id():
    return current_account().id

lib.audit_mixin.current_user_id = current_user_id

```

## In each class that you want to track audits

    @classmethod
    def audit_actions(cls):
        return [lib.audit_mixin.ACTION_UPDATE]


The above code tracks update events. If you want to track creation and deletion, then you can add them to the list.


## Install the audit table

    python scripts/add-audit-trail-tables.py stage/1-dev/

where `stage/1-dev` is the directory with the config files for your Reahl app.

## That's it

Enjoy.



# References

* https://gist.github.com/ngse/c20058116b8044c65d3fbceda3fdf423
* https://github.com/reahl/reahl/issues/213
