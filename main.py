import uvicorn
from datetime import timedelta,datetime
from pymongo import MongoClient
import bcrypt
import jwt
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware, db
from access_token import create_access_token,decode_access_token        
from graphql import GraphQLError
from schema import Login as SchemaUser
from database_conf import db_session
from schema import Login
from models import Login as ModelUser
from pydantic import BaseModel
from fb_enhancement import get_latest_enhancement, get_total_enhancement, get_active_fb_account_info
from starlette.graphql import GraphQLApp
import os
import models
import graphene
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv('.env')

DB = "fb_details"
MSG_COLLECTION = "fb_user_details"

db = db_session.session_factory()

app = FastAPI()

sched = BackgroundScheduler(timezone="Asia/kolkata")

# to avoid csrftokenError
app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])


class Query(graphene.ObjectType):

    all_posts = graphene.List(ModelUser)
    post_by_id = graphene.Field(ModelUser, post_id=graphene.Int(required=True))

    def resolve_all_posts(self, info):
        query = ModelUser.get_query(info)
        return query.all()

    def resolve_post_by_id(self, info, post_id):
        return db.query(models.Post).filter(models.Login.id == post_id).first()



class AuthenticateUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    result = graphene.Boolean()
    token = graphene.String()

    @staticmethod
    def mutate(root, info, email, password):
        user = SchemaUser(email=email, password=password)
        db_user_info = db.query(models.Login).filter(models.Login.email == email).one_or_none()
        if db_user_info is None:
            raise GraphQLError("No user exists")
        if bcrypt.checkpw(user.password.encode("utf-8"), db_user_info.password.encode("utf-8")):
            access_token_expires = timedelta(minutes=60)
            access_token = create_access_token(data={"user": email}, expires_delta=access_token_expires)
            result = True
            return AuthenticateUser(result=result, token=access_token)
        else:
            result = False
            return AuthenticateUser(result=result)


class CreateNewUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)
    result = graphene.Boolean()

    @staticmethod
    def mutate(root, info, email, password):

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        password_hash = hashed_password.decode("utf8")
        confirm_password_hash = hashed_password.decode("utf8")
        user = SchemaUser(email=email, password=password_hash)
        db_user = models.Login(email=user.email, password=password_hash)
        if db_user :
            raise GraphQLError("Email already exists")
        if password_hash != confirm_password_hash:
             raise GraphQLError("password and confirm password must be same")
        db.add(db_user)

        try:
            db.commit()
            db.refresh(db_user)
            result = True
            return CreateNewUser(result=result)

        except:
            db.rollback()
            raise

class FBAccount_details(graphene.Mutation):
    class Arguments:
        account_name  = graphene.String(required=True)
        account_id = graphene.String(required=True)
        token = graphene.String(required=True)

    result = graphene.String()

    @staticmethod
    def mutate(root, info, account_name, account_id, token):

        try:
            payload = decode_access_token(data=token)
            email = payload.get("user")

            if email is None:
                raise GraphQLError("Invalid credentials")

        except jwt.PyJWTError:
            raise GraphQLError("Invalid credentials")

        user = db.query(models.Login).filter(models.Login.email == email).first()

        if user is None:
            raise GraphQLError("Invalid credentials")
        with MongoClient() as client:
            msg_collection = client[DB][MSG_COLLECTION]
            data = {
                "account_name":account_name,
                "account_id":account_id
            }
            result = msg_collection.insert_one(data)
            ack = result.acknowledged
            result ="Fb accounts addded successfully"
            return FBAccount_details(result=result)
       

class FBMutations(graphene.ObjectType):
    authenticate_user = AuthenticateUser.Field()
    create_new_user = CreateNewUser.Field()
    PostAccount_details = FBAccount_details.Field()

@app.get("/api/get_active_fb_info")
async def root():
    data = get_active_fb_account_info()
    return data

class enhancement_payload(BaseModel):
    from_date: str
    to_date: str


@app.post("/api/get_latest_enhancement")
async def get_latest_enhancement(item:enhancement_payload ):
    dict_item = item.dict()
    from_date = dict_item['from_date']
    to_date = dict_item['to_date']
    data = get_latest_enhancement(from_date,to_date)
    return data

def start_job():
    data = get_total_enhancement()
    with MongoClient() as client:
        msg_collection = client[DB][MSG_COLLECTION]
        result = msg_collection.insert_one(data) 
        ack = result.acknowledged

def end_job():
    data = get_total_enhancement()
    with MongoClient() as client:
        msg_collection = client[DB][MSG_COLLECTION]
        result = msg_collection.insert_one(data)
        ack = result.acknowledged

@app.on_event('startup')
def init_data():
    sched.add_job(start_job, 'cron', hour=2, minute=30)
    sched.add_job(end_job, 'cron', hour=14, minute=30)
    sched.start()

app.add_route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query, mutation=FBMutations)))