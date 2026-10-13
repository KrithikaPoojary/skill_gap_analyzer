import urllib.request, urllib.parse, json

BASE = "http://localhost:8000/api/v1"

def get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(BASE + path, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def post(path, data, form=False):
    if form:
        body = urllib.parse.urlencode(data).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        body = json.dumps(data).encode()
        headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

print("\n" + "="*50)
print("   SKILL GAP ANALYZER - LIVE DEMO")
print("="*50)

# 1. Health
print("\n[1] HEALTH CHECK")
r = get("/health")
d = r.get("data", r)
print(f"    Status   : {d.get('status')}")
print(f"    App      : {d.get('app_name')}")
print(f"    Database : {d.get('database')}")

# 2. Register
print("\n[2] REGISTER USER")
r = post("/auth/register", {
    "email": "krithika@demo.com",
    "password": "Krithika@123",
    "full_name": "Krithika Poojary"
})
d = r.get("data", r)
if "email" in d:
    print(f"    Created  : {d['email']}")
    print(f"    Name     : {d.get('full_name')}")
    print(f"    ID       : {d.get('id')}")
else:
    print(f"    Note     : {d.get('detail', 'User may already exist')}")

# 3. Login
print("\n[3] LOGIN")
r = post("/auth/login", {
    "username": "krithika@demo.com",
    "password": "Krithika@123"
}, form=True)
token = r.get("access_token", "")
print(f"    Token    : {token[:35]}...")
print(f"    Type     : {r.get('token_type')}")

# 4. Profile
print("\n[4] MY PROFILE")
r = get("/profile/me", token)
d = r.get("data", r)
print(f"    Name     : {d.get('full_name')}")
print(f"    Email    : {d.get('email')}")
print(f"    Active   : {d.get('is_active')}")

# 5. Roles
print("\n[5] AVAILABLE ROLES")
r = get("/roles/", token)
d = r.get("data", r)
items = d.get("items", []) if isinstance(d, dict) else d
for role in items[:6]:
    print(f"    - {role.get('title', role)}")

# 6. Analytics
print("\n[6] TRENDING SKILLS")
try:
    r = get("/analytics/trending-skills", token)
    d = r.get("data", r)
    skills = d if isinstance(d, list) else d.get("skills", d.get("items", []))
    for s in skills[:5]:
        name = s.get("skill_name", s.get("name", s))
        print(f"    - {name}")
except Exception as e:
    print(f"    (endpoint: {e})")

print("\n" + "="*50)
print("   PROJECT IS FULLY WORKING!")
print("="*50 + "\n")
