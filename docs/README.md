# Django Extensible Models Experiment

This repository holds some experimental code to try and allow for
dynamic extensions of Django models based on structured data in
JSONFields.

It is a playground for me to try out ideas while I clarify concepts.
To help with playing with me, I have checked in an SQLite database
into the repository to give you some sample data.

## How does it work?

The main idea is that every Model you want extended is now augmented
with two new `JSONField`s: `extra` and `extra_schema`. `extra_schema`
contains a schema that follows the [JSON
Schema](https://json-schema.org) specification. This is used to
auto-generate forms, handle validation, auto-generate Django Rest
Framework Serializers, ...

This idea generally handles most cases except migrations that I am
continuing to think about. If you have any ideas, do let me know.

## How to use this code

You download the code in this repository (by using the big green
`Code` button on this project‘s GitHub page) and navigate into it.

When in the folder, do the following:

````
python -m venv venv
source venv/bin/activate
cd src
./manage.py runserver
````

And then go visit
[http://localhost:8000/contacts/](http://localhost:8000/contacts/) to
see the app in practice. If you want to access the Django admin, head
to [http://localhost:8000/admin/](http://localhost:8000/admin/) and
use the credentials `username: harish, password: harish`.

## Copyright and license

Copyright (c) 2022 [Harish Narayanan](https://harishnarayanan.org).

This code is licenced under the MIT Licence. See
[LICENSE](https://github.com/hnarayanan/django-extensible-models-experiment/blob/main/LICENSE)
for the full text of this licence.
