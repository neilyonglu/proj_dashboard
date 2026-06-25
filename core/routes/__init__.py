def register_routes(app):
    from . import main, projects, tasks, admin, manage
    main.register(app)
    projects.register(app)
    tasks.register(app)
    admin.register(app)
    manage.register(app)
