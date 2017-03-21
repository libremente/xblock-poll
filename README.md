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
