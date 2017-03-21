# Modified version of the Xblock Poll to test translations

## Mods
* Added the `@XBlock.needs('i18n')` decorator in `poll.py`.
* Added the `{% load i18n %}` template tag in the main poll.html template.
* Added some dummy text to check the translations

```html
<div>
  <p>Below this point, if the translation system works, you should see: `THIS TEXT HAS BEEN TRANSLATED` 4 times and <b>NOT</b> `TRANSLATE ME` <p>
  <p>--------------------------</p>
  <p>{% trans "TRANSLATE ME" %}</p>
  <p>{% trans "TRANSLATE ME" %}</p>
  <p>{% trans "TRANSLATE ME" %}</p>
  <p>{% trans "TRANSLATE ME" %}</p>
  <p>--------------------------</p>
</div>
```

* Added the locale folder containing the `.po`. and `.mo` files for
  translation.

## Warning
This implementation does not follow the standard i18n guidelines for Xblocks
which need to have a `translation` folder near the main `<xblock_name.py>` file
and inside the `<lang_code>/LC_MESSAGES` the `text.po` and `text.mo`. This one
has a `locale` folder and the couple `django.po` and `django.mo` file since we
are testing another translation solution. 


## Adding the XBlock path to the platform's LOCALE

Add in the `startup.py` file the following function:

```python
def enable_xblock_path():
    xblocks_root = settings.ENV_ROOT / "<xblock-path>/xblock-poll/poll"
    settings.LOCALE_PATHS = (xblocks_root / "locale",) + settings.LOCALE_PATHS
    print "####################################################################"
    print settings.LOCALE_PATHS
```

and call the function after `microsite.enable_microsites(log)`
