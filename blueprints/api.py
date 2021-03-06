import app
import datetime
import flask
import iso8601
import pytz

page = flask.Blueprint('api', __name__)
require_login = app.hooks.require_login

with_venue_list = app.hooks.with_venue_list

def _stock_response(ok, api):
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": api.last_error()
    })

@page.route('/api/my/conferences')
@require_login
def my_conferences():
    confs = flask.g.api.list_conference(
        lang=flask.g.lang,
        organizers=[flask.g.stash.get('user').get('id')],
        status=['any']
    )
    return flask.jsonify(confs)

@page.route('/api/venue/list')
@require_login
@with_venue_list
def venue_list():
    return flask.jsonify(flask.g.stash.get('venues'))

@page.route('/api/venue/delete', methods=['POST'])
@require_login
def venue_delete():
    ok = flask.g.api.delete_venue(
        id=flask.request.values.get('id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return _stock_response(ok, flask.g.api)

@page.route('/api/venue/room/add', methods=['POST'])
@require_login
def venue_room_add():
    vals = flask.request.values
    args = {}
    for k in vals:
        args[k] = vals[k]
    args['capacity'] = float(args['capacity']) # numify
    args['user_id'] = flask.g.stash.get('user').get('id')
    ok = flask.g.api.create_room(**args)
    return _stock_response(ok, flask.g.api)

@page.route('/api/user/incremental')
@require_login
def user_incremental():
    users = flask.g.api.list_user(pattern=flask.request.args.get('query'))
    return flask.jsonify({
        "suggestions": map(lambda x: {"data":x.get('id'),"value": "%s (%s)" % (x.get('nickname'), x.get('auth_via')) }, users)
    })

@page.route('/api/conference/list')
@require_login
def conference_list():
    args = flask.request.args
    conferences = flask.g.api.list_conference(
        lang=flask.g.lang,
        **args
    )
    return flask.jsonify(conferences)

@page.route('/api/conference/featured_speaker/list')
@require_login
def list_conference_featured_speaker():
    confs = flask.g.api.list_featured_speakers(
        conference_id=flask.request.values.get('conference_id'),
        lang=flask.request.values.get('lang'),
        limit=flask.request.values.get('limit'),
        since=flask.request.values.get('since'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return flask.jsonify(confs)

@page.route('/api/conference/featured_speaker/add', methods=['POST'])
@require_login
def add_conference_featured_speaker():
    args = {}
    args['user_id'] = flask.g.stash.get('user').get('id')
    for k in ['conference_id', 'avatar_url', 'description', 'speaker_id', 'display_name', 'description#ja']:
        args[k] = flask.request.values.get(k)

    ok = flask.g.api.add_featured_speaker(**args)
    return _stock_response(ok, flask.g.api)

@page.route('/api/conference/featured_speaker/remove', methods=['POST'])
@require_login
def remove_conference_featured_speaker():
    ok = flask.g.api.delete_featured_speaker(
        id=flask.request.values.get('id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/conference/sponsor/list')
@require_login
def list_conference_sponsor():
    confs = flask.g.api.list_sponsors(
        conference_id=flask.request.values.get('conference_id'),
        lang=flask.request.values.get('lang'),
        limit=flask.request.values.get('limit'),
        since=flask.request.values.get('since')
    )
    return flask.jsonify(confs)

@page.route('/api/conference/sponsor/add', methods=['POST'])
@require_login
def add_conference_sponsor():
    args = {}
    args['user_id'] = flask.g.stash.get('user').get('id')
    for k in ['conference_id','logo_url','url','name', 'name#ja','group_name']:
        args[k] = flask.request.values.get(k)
    if 'sort_order' in flask.request.values:
        v = flask.request.values.get('sort_order')
        if v:
            args['sort_order'] = int(v)

    ok = flask.g.api.add_sponsor(**args)
    return _stock_response(ok, flask.g.api)

@page.route('/api/conference/sponsor/remove', methods=['POST'])
@require_login
def remove_conference_sponsor():
    ok = flask.g.api.delete_sponsor(
        id=flask.request.values.get('id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/conference/administrator/list')
@require_login
def list_conference_administrator():
    confs = flask.g.api.list_conference_admin(
        conference_id=flask.request.values.get('conference_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return flask.jsonify(confs)

@page.route('/api/conference/administrator/add', methods=['POST'])
@require_login
def add_conference_administrator():
    ok = flask.g.api.add_conference_admin(
        conference_id=flask.request.values.get('conference_id'),
        admin_id=flask.request.values.get('user_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return _stock_response(ok, flask.g.api)

@page.route('/api/conference/administrator/remove', methods=['POST'])
@require_login
def remove_conference_administrator():
    ok = flask.g.api.delete_conference_admin(
        conference_id=flask.request.values.get('conference_id'),
        admin_id=flask.request.values.get('admin_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/conference/date/list')
@require_login
def list_conference_date():
    dates = flask.g.api.list_conference_date(
        conference_id=flask.request.values.get('conference_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return flask.jsonify(dates)

@page.route('/api/conference/date/add', methods=['POST'])
@require_login
def add_conference_date():
    # normalize this datetime into UTC
    conference_id = flask.request.values.get('conference_id')
    conference = flask.g.api.lookup_conference(id=conference_id, lang=flask.g.lang)
    localtz = pytz.timezone(conference.get('timezone', 'UTC'))

    offset = localtz.utcoffset(datetime.datetime.utcnow())
    open_time = iso8601.parse_date(
        '%sT%s%s%02d%02d' % (
            flask.request.values.get('date'),
            flask.request.values.get('start_time'),
            '+' if offset.total_seconds() > 0 else '-',
            int(offset.total_seconds() / 3600),
            int((offset.total_seconds() % 3600) / 600),
        )
    )
    end_time = iso8601.parse_date(
        '%sT%s%s%02d%02d' % (
            flask.request.values.get('date'),
            flask.request.values.get('end_time'),
            '+' if offset.total_seconds() > 0 else '-',
            int(offset.total_seconds() / 3600),
            int((offset.total_seconds() % 3600) / 600),
        )
    )

    ok = flask.g.api.add_conference_date(
        conference_id=conference_id,
        date={
            "open": open_time.isoformat(),
            "close": end_time.isoformat()
        },
        user_id=flask.g.stash.get('user').get('id')
    )

    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })
 

@page.route('/api/conference/venue/add', methods=['POST'])
@require_login
def add_conference_venue():
    ok = flask.g.api.add_conference_venue(
        conference_id=flask.request.values.get('conference_id'),
        venue_id=flask.request.values.get('venue_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/conference/venue/delete', methods=['POST'])
@require_login
def delete_conference_venue():
    ok = flask.g.api.delete_conference_venue(
        conference_id=flask.request.values.get('conference_id'),
        venue_id=flask.request.values.get('venue_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/track/create', methods=['POST'])
@require_login
def create_track():
    ok = flask.g.api.create_track(
        conference_id=flask.request.values.get('conference_id'),
        room_id=flask.request.values.get('room_id'),
        name=flask.request.values.get('name'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/track/delete', methods=['POST'])
@require_login
def delete_track():
    ok = flask.g.api.delete_track(
        id=flask.request.values.get('id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })

@page.route('/api/session/bulk_update', methods=['POST'])
@require_login
def update_session_bulk():
    errors = []
    for session_id in flask.request.json:
        data = flask.request.json[session_id]
        for k in data:
            ok = flask.g.api.update_session(id=k, **data[k])
            if not ok:
                errors.append(flask.g.api.last_error())

    if len(errors) == 0:
        return flask.jsonify({"success": True})
    return flask.jsonify({
        "success": False,
        "error": errors
    })

@page.route('/api/conference/staff/list')
@require_login
def list_conference_staff():
    confs = flask.g.api.list_conference_staff(
        conference_id=flask.request.values.get('conference_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return flask.jsonify(confs)

@page.route('/api/conference/staff/add', methods=['POST'])
@require_login
def add_conference_staff():
    ok = flask.g.api.add_conference_staff(
        conference_id=flask.request.values.get('conference_id'),
        staff_id=flask.request.values.get('user_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    return _stock_response(ok, flask.g.api)

@page.route('/api/conference/staff/remove', methods=['POST'])
@require_login
def remove_conference_staff():
    ok = flask.g.api.delete_conference_staff(
        conference_id=flask.request.values.get('conference_id'),
        staff_id=flask.request.values.get('staff_id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        return flask.jsonify({
            "success": True
        })
    return flask.jsonify({
        "success": False,
        "error": flask.g.api.last_error()
    })


