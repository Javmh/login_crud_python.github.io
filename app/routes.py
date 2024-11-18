# from flask import render_template, request, redirect, url_for
# from app import app, db
# from app.forms import LoginForm

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     form = LoginForm()
#     if form.validate_on_submit():
#         # Aquí iría la lógica para validar las credenciales del usuario
#         # y redirigir a la página de inicio si son correctas
#         return redirect(url_for('home'))
#     return render_template('index.html', title='Inicio de Sesión', form=form)