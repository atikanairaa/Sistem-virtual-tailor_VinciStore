from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()
ctx = app.app_context()
ctx.push()
db.session.execute(text('ALTER TABLE carts MODIFY COLUMN fit_status VARCHAR(50);'))
db.session.execute(text('ALTER TABLE carts MODIFY COLUMN body_shape VARCHAR(50);'))
db.session.commit()
print('DB updated')
ctx.pop()
