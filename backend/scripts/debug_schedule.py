from app import create_app
from app.models.models import Schedule, User, Role
from sqlalchemy import or_

app = create_app()

with app.app_context():
    print("--- Live Debug ---")
    current_user_id = 2 # ztx
    
    # Check if Schedule 4 exists
    s = Schedule.query.get(4)
    if s:
        print(f"Schedule 4 found. User ID: {s.user_id}")
        u = User.query.get(s.user_id)
        if u:
            print(f"Schedule Creator: {u.username}, Role ID: {u.role_id}")
            if u.role_rel:
                print(f"Creator Role Code: {u.role_rel.code}")
            else:
                print("Creator Role Rel MISSING")
        else:
            print("Schedule Creator NOT FOUND")
    else:
        print("Schedule 4 NOT FOUND")
        
    print(f"--- Querying for User {current_user_id} ---")
    query = Schedule.query.join(User).outerjoin(Role).filter(
        or_(
            Schedule.user_id == current_user_id,
            Role.code == 'admin'
        )
    )
    print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))
    res = query.all()
    print(f"Results: {len(res)}")
    for r in res:
        print(f" - {r.id}: {r.title}")
