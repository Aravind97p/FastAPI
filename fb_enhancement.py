import requests
import os

def get_total_shares(post_id):
    url = "https://graph.facebook.com/v15.0/"+str(post_id)+"/"
    headers =  {"Content-Type":"application/json"}
    parameters ={
        'access_token':os.environ["FB_ACCESS_KEY"],
        'fields':"shares,comments",
    }
    response= requests.get(url, headers=headers,params=parameters).json()
    return response

def get_total_likes(post_id):
    url = "https://graph.facebook.com/v15.0/"+str(post_id)+"/"
    headers =  {"Content-Type":"application/json"}
    parameters ={
        'access_token':os.environ["FB_ACCESS_KEY"],
        'fields':"reactions.type(LIKE).summary(total_count),insights.metric(post_reactions_by_type_total)",
    }
    response= requests.get(url, headers=headers,params=parameters).json()
    return response



def get_latest_enhancement(from_date,to_date):
    url = "https://graph.facebook.com/v15.0/"+os.environ["FB_ACCOUNT_ID"]+"/posts"
    headers =  {"Content-Type":"application/json"}
    parameters ={
        'access_token':os.environ["FB_ACCESS_KEY"],
        'since':from_date,
        'until':to_date
    }
    response= requests.get(url, headers=headers,params=parameters).json()
    if len(response['data']) != 0:
        latest_post_id = response['data'][0]['id']
        likes_count = get_total_likes(latest_post_id)
        try:
            likes_count = likes_count['reactions']['summary']['total_count']
        except:
            likes_count = 0
        share_comment_response = get_total_shares(latest_post_id)
        try:
            share_count = share_comment_response['shares']['count']
        except:
            share_count = 0
        try:
            comment_count = share_comment_response['comments']['count']
        except:
            comment_count = 0
        data = {
            "latest_enhancement_date":response['data'][0]['created_time'],
            "likes_count":likes_count,
            "share_count":share_count,
            "comment_count":comment_count
        }
    else:
        data = {
            "message":"No data Found",
        }
    return data

def get_total_enhancement():
    url = "https://graph.facebook.com/v15.0/me"
    headers =  {"Content-Type":"application/json"}
    parameters ={
        'access_token':os.environ["FB_ACCESS_KEY"],
        'fields':"posts{id,actions,from,promotable_id,status_type,reactions{type}},likes{fan_count,about,followers_count,id}"
    }
    response= requests.get(url, headers=headers,params=parameters).json()
    return response

def get_active_fb_account_info():

    url = "https://graph.facebook.com/v15.0/"+os.environ["FB_ACCOUNT_ID"]+"/"
    headers =  {"Content-Type":"application/json"}
    parameters ={
        'access_token':os.environ["FB_ACCESS_KEY"],
        'fields':"id,name,birthday,about,education,email,gender,location"
    }
    response= requests.get(url, headers=headers,params=parameters).json()
    return response