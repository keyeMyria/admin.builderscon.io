import admin
import base64
import flask
import flasktools
import flask_oauth
import hooks
import json
import re
import traceback

_oauth = flask_oauth.OAuth()

twitter = _oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=admin.cfg.section('TWITTER').get('client_id'),
    consumer_secret=admin.cfg.section('TWITTER').get('client_secret').encode('ASCII')
)

# Used for three-legged OAuth
twitter_app = _oauth.remote_app('twitter_app',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=admin.cfg.section('TWITTER').get('client_id'),
    consumer_secret=admin.cfg.section('TWITTER').get('client_secret').encode('ASCII')
)

facebook = _oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=admin.cfg.section('FACEBOOK').get('client_id'),
    consumer_secret=admin.cfg.section('FACEBOOK').get('client_secret').encode('ASCII'),
    request_token_params={'scope': 'email'}
)
github = _oauth.remote_app('github',
    base_url='https://api.github.com',
    request_token_url=None,
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    consumer_key=admin.cfg.section('GITHUB').get('client_id'),
    consumer_secret=admin.cfg.section('GITHUB').get('client_secret').encode('ASCII'),
    request_token_params={'scope': ''}
)

@github.tokengetter
def get_github_token(token=None):
    return flask.session.get('github_token')

@facebook.tokengetter
def get_facebook_token(token=None):
    return flask.session.get('facebook_token')

@twitter.tokengetter
def get_twitter_token(token=None):
    return flask.session.get('twitter_token')

def start(oauth_handler, callback):
    print("starting handler with callback %s" % callback)
    try:
        args = {}
        if flask.request.args.get('.next'):
            args['.next'] = flask.request.args.get('.next')

        if len(args.keys()) > 0:
            callback = '%s?%s' % (callback, flasktools.urlencode(args))

        return oauth_handler.authorize(callback=callback)
    except BaseException as e:
        print(traceback.format_exc())
        raise e
    
@github.authorized_handler
def github_callback(resp):
    if resp is None:
        err = flask.request.args.get('error_description') or flask.request.args.get('error')
        return flask.render_template('auth/login.html', error=err)
    if 'error' in resp:
        err = resp.get('error_description') or resp.get('error')
        return flask.render_template('auth/login.html', error=err)

    flask.session['github_token'] = (
        resp['access_token'],
        ''
    )
    res = github.request('user')
    if res.status != 200:
        print("got status %d" % res.status)
        print(res.data)
        return flask.render_template('auth/login.html', error='failed to fetch user information after oauth')

    data = res.data

    # Load user via github id
    user = flask.g.api.lookup_user_by_auth_user_id(auth_via='github', auth_user_id=str(data['id']))
    if user:
        flask.session['user_id'] = user.get('id')
        flask.session['access_token'] = resp['access_token']
        flask.session['auth_via'] = 'github'
        flask.g.stash['user'] = user
        return flask.redirect(flask.request.args.get('.next') or '/')

    names = re.compile('\s+').split(data.get('name'))
    first_name = 'Unknown'
    last_name = 'Unknown'
    if len(names) > 1:
        first_name = names[0]
        last_name = names[-1]
    elif len(names) == 1:
        first_name = names[0]

    user = flask.g.api.create_user (
        str(data.get('id')),
        auth_via='github',
        nickname=data.get('login'),
        first_name=first_name,
        last_name=last_name,
        avatar_url='https://avatars.githubusercontent.com/u/' + str(data.get('id'))
    )
    if not user:
        return flask.render_template('auth/login.html', error='failed to register user in the backend server')

    flask.session['user_id'] = user.get('id')
    flask.session['access_token'] = resp['access_token']
    flask.session['auth_via'] = 'github'
    flask.g.stash['user'] = user

    return redirect_edit()

def redirect_edit():
    # Redirect user to edit page, so that they can choose their
    # language/timezone settings
    return flask.redirect(
        '/user/edit?%s' % flasktools.urlencode({
            'setup': 1,
            '.next': flask.request.args.get('.next')
        })
    )

@facebook.authorized_handler
def facebook_callback(resp):
    if resp is None:
        err = flask.request.args.get('error_description') or flask.request.args.get('error')
        return flask.render_template('auth/login.html', error=err)

    flask.session['facebook_token'] = (
        resp['access_token'],
        ''
    )
    res = facebook.request('me')
    if res.status != 200:
        print("got status %d" % res.status)
        print(res.data)
        return flask.render_template('auth/login.html', error='failed to fetch user information after oauth')

    data = res.data

    # Load user via facebook id
    user = flask.g.api.lookup_user_by_auth_user_id(auth_via='facebook', auth_user_id=data['id'])
    if user:
        flask.session['user_id'] = user.get('id')
        flask.session['access_token'] = resp['access_token']
        flask.session['auth_via'] = 'facebook'
        flask.g.stash['user'] = user
        return flask.redirect(flask.request.args.get('.next') or '/')

    names = re.compile('\s+').split(data.get('name'))
    first_name = 'Unknown'
    last_name = 'Unknown'
    if len(names) > 1:
        first_name = names[0]
        last_name = names[-1]
    elif len(names) == 1:
        first_name = names[0]

    params = dict({
        'height':130,
        'width': 130,
        'fields': 'url',
        'redirect': False
    })
    res = facebook.request('v2.7/me/picture', data=params)
    if res.status != 200:
        print("got status %d" % res.status)
        print(res.data)
        return flask.render_template('auth/login.html', error='failed to fetch user photo after oauth')
    picture = res.data

    user = flask.g.api.create_user (
        data.get('id'),
        auth_via='facebook',
        nickname=data.get('name'),
        first_name=first_name,
        last_name=last_name,
        avatar_url=picture.get('data', dict()).get('url')
    )
    if not user:
        return flask.render_template('auth/login.html', error='failed to register user in the backend server')

    flask.session['user_id'] = user.get('id')
    flask.session['access_token'] = resp['access_token']
    flask.session['auth_via'] = 'facebook'
    flask.g.stash['user'] = user

    return redirect_edit()

@twitter.authorized_handler
def twitter_callback(resp):
    if resp is None:
        err = flask.request.args.get('error_description') or flask.request.args.get('error')
        return flask.render_template('auth/login.html', error=err)

    flask.session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    consumer_key=admin.cfg.section('TWITTER').get('client_id')
    consumer_secret=admin.cfg.section('TWITTER').get('client_secret').encode('ASCII')

    # Load user via twitter id
    user = flask.g.api.lookup_user_by_auth_user_id(auth_via='twitter', auth_user_id=resp['user_id'])
    if user:
        flask.session['user_id'] = user.get('id')
        flask.session['access_token'] = ":".join([resp['oauth_token'], resp['oauth_token_secret'], consumer_key, consumer_secret])
        flask.session['auth_via'] = 'twitter'
        flask.g.stash['user'] = user
        return flask.redirect(flask.request.args.get('.next') or '/')

    res = twitter.request('account/verify_credentials.json')
    if res.status != 200:
        print("got status %d" % res.status)
        print(res.data)
        return flask.render_template('auth/login.html', error='failed to fetch user information after oauth')

    data = res.data

    avatar_url = data.get('profile_image_url')
    if avatar_url:
        avatar_url = re.compile('_normal\.').sub('_bigger.', avatar_url)

    names = re.compile('\s+').split(data.get('name'))
    first_name = 'Unknown'
    last_name = 'Unknown'
    if len(names) > 1:
        first_name = names[0]
        last_name = names[-1]
    elif len(names) == 1:
        first_name = names[0]

    user = flask.g.api.create_user (
        data.get('id_str'),
        auth_via='twitter',
        nickname=data.get('screen_name'),
        avatar_url=avatar_url, 
        first_name=first_name,
        last_name=last_name,
    )
    if not user:
        return flask.render_template('auth/login.html', error='failed to register user in the backend server')

    flask.session['user_id'] = user.get('id')
    flask.session['access_token'] = ":".join([resp['oauth_token'], resp['oauth_token_secret'], consumer_key, consumer_secret])
    flask.session['auth_via'] = 'twitter'
    flask.g.stash['user'] = user
    return redirect_edit()

@admin.app.route('/conference/<id>/twitter/authenticate')
@hooks.with_conference
def auth_conference_twitter():
    if 'twitter_app_token' in flask.session:
        del flask.session['twitter_app_token']
    id = flask.g.stash['conference_id']
    return start(twitter_app, admin.app.base_url + '/conference/twitter/callback?conference_id='+id)

@twitter_app.tokengetter
def get_twitter_app_token(token=None):
    return flask.session.get('twitter_app_token')

@admin.app.route('/conference/twitter/callback')
@twitter_app.authorized_handler
def twitter_app_callback(resp):
    if resp is None:
        err = flask.request.args.get('error_description') or flask.request.args.get('error')
        return flask.render_template('conference/twitter/authfail.html', error=err)

    conference_id = flask.request.args.get('conference_id')
    data = dict(
        access_token=resp['oauth_token'],
        access_token_secret=resp['oauth_token_secret']
    )
    ok = flask.g.api.add_conference_credential(
        conference_id=conference_id,
        data=base64.b64encode(json.dumps(data)),
        type='twitter'
    )
    if not ok:
        return "failure" # TODO

    if 'twitter_app_token' in flask.session:
        del flask.session['twitter_app_token']
    return flask.redirect('/conference/%s/twitter' % conference_id)
