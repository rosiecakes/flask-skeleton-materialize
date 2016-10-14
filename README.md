# Flask Skeleton

Adapted from [https://github.com/realpython/flask-skeleton/tree/master/project](https://github.com/realpython/flask-skeleton/tree/master/project)  
Using Materialize CSS

## Quick Start

### Basics

1. Activate a virtualenv
1. Install the requirements

### Set Environment Variables

Update *project/server/config.py*, and then run:

```sh
$ export APP_SETTINGS="project.server.config.DevelopmentConfig"
```

or

```sh
$ export APP_SETTINGS="project.server.config.ProductionConfig"
```

### Create DB

```sh
$ python manage.py create_db
$ python manage.py db init
$ python manage.py db migrate
$ python manage.py create_admin
$ python manage.py create_data
```

### Run the Application

```sh
$ python manage.py runserver
```

So access the application at the address [http://localhost:5000/](http://localhost:5000/)

### Testing

Without coverage:

```sh
$ python manage.py test
```

With coverage:

```sh
$ python manage.py cov
```
