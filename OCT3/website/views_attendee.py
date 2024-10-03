from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from .models import Note, Events11, Users6, Attendee_events6, Client_events4, Supplier_info6, Event_records2, Attendee_records2
from . import db, socketio
from .gen_algo_final import *
import json, csv
from flask_socketio import join_room, leave_room, send, emit
from datetime import datetime
from .views_creator import rooms

views_attendee = Blueprint('views_attendee', __name__)

@views_attendee.route('/create_event_profile_attendee')
@login_required
def create_event_profile():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
###################################################################################################################################################################################
@views_attendee.route("/video_chat_dashboard_attendee", methods=["POST", "GET"])
@login_required
def video_chat_dashboard_attendee():
    return render_template("video_chat_dashboard.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

@views_attendee.route("/video_join_meeting_attendee", methods=["POST", "GET"])
@login_required
def video_join_meeting_attendee():
    if request.method == "POST":
        room_id = request.form.get("roomID")
        return redirect(f"/video_create_meeting?roomID={room_id}")
    return render_template("video_join_meeting.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)
####################################################################################################################################################################################
@views_attendee.route("/join_room_attendee", methods=["POST", "GET"])
@login_required
def join_room_view():
    """Page where users enter the room code to join."""
    session.clear()
    attendee = Events11.query.all()  # Query all events
    if request.method == "POST":
        code = request.form.get("code")
        if not code:
            return render_template("join_room.html", error="Please enter a room code.", user=current_user, role=current_user.role, name=current_user.first_name)

        if code not in rooms:
            return render_template("join_room.html", error="Room does not exist.", user=current_user, role=current_user.role, name=current_user.first_name)

        session["room"] = code
        session["name"] = current_user.first_name  # Use the user's first name
        return redirect(url_for('views_attendee.room'))

    return render_template("join_room.html", user=current_user, role=current_user.role, name=current_user.first_name, attendee=attendee)

@views_attendee.route("/room")
@login_required
def room():
    """Chat room view."""
    room_code = session.get("room")
    if room_code is None or room_code not in rooms:
        return redirect(url_for("views_attendee.join_room_view"))

    return render_template("room.html", user=current_user, code=room_code, messages=rooms[room_code]["messages"], role=current_user.role, name=current_user.first_name)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    if room not in rooms:
        return 

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    rooms[room]["messages"].append(content)  # Store message in the room
    send(content, to=room)  # Emit message to room
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    
    if room not in rooms:
        return  # Ignore if room does not exist
    
    join_room(room)
    rooms[room]["members"] += 1
    send({"name": name, "message": "has entered the room"}, to=room)
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        send({"name": name, "message": "has left the room"}, to=room)
        print(f"{name} has left the room {room}")

######################################################################################################################################################### Attendee
@views_attendee.route('/attendee', methods=['GET', 'POST'])
def attendee():
    return render_template('attendee.html', user=current_user, name=current_user.first_name)

@views_attendee.route('/attendee_invites', methods=['GET', 'POST'])
@login_required
def attendee_invites():

    # Get the invites stored in the Attendee_events6 table
    attendee_event = Attendee_events6.query.filter_by(user_id=current_user.id).first()
    
    invited_events = []
    if attendee_event and attendee_event.invites:
        invited_events = json.loads(attendee_event.invites)

    return render_template('attendee_invites.html', user=current_user, name=current_user.first_name, invited_events=invited_events)

@views_attendee.route('/accept_invite', methods=['POST'])
@login_required
def accept_invite():
    event_name = request.form.get('event_name')
    
    # Find the event in the Events11 table
    event = Events11.query.filter_by(event_name=event_name).first()
    
    if event:
        # Add this event to the current user's RSVP events in Attendee_events6
        attendee_event = Attendee_events6.query.filter_by(user_id=current_user.id).first()
        if attendee_event:
            rsvp_events = json.loads(attendee_event.rsvp_events) if attendee_event.rsvp_events else []
            rsvp_events.append({
                'event_name': event.event_name,
                'event_desc': event.event_desc,
                'room_code': event.room_code,
                'start_date': str(event.start_date),
                'end_date': str(event.end_date),
                'event_privacy': event.event_privacy
            })
            attendee_event.rsvp_events = json.dumps(rsvp_events)

            # Save the event in Attendee_records2 when attendee accepts
            new_attendee_record = Attendee_records2(
                event_name=event.event_name,
                event_desc=event.event_desc,
                event_privacy=event.event_privacy,
                start_date=event.start_date,
                end_date=event.end_date,
                attendee_id=current_user.id  # Save the attendee's user ID
            )
            db.session.add(new_attendee_record)

            db.session.commit()

            # Remove the accepted event from invites
            invites = json.loads(attendee_event.invites) if attendee_event.invites else []
            updated_invites = [inv for inv in invites if inv['event_name'] != event_name]
            attendee_event.invites = json.dumps(updated_invites)

        else:
            # Create a new entry for the attendee if it doesn't exist
            new_attendee_event = Attendee_events6(
                user_id=current_user.id,
                rsvp_events=json.dumps([{
                    'event_name': event.event_name,
                    'event_desc': event.event_desc,
                    'room_code': event.room_code,
                    'start_date': str(event.start_date),
                    'end_date': str(event.end_date),
                    'event_privacy': event.event_privacy
                }]),
                invites=json.dumps([])  # Initialize invites as empty if needed
            )
            db.session.add(new_attendee_event)

        # Add the user's details to the event's RSVP attendees in Events11
        rsvp_attendees = json.loads(event.rsvp_attendees) if event.rsvp_attendees else []
        rsvp_attendees.append({
            'attendee_name': current_user.first_name,
            'attendee_lname': current_user.last_name,
            'attendee_email': current_user.email
        })
        event.rsvp_attendees = json.dumps(rsvp_attendees)

        db.session.commit()
    
    return redirect(url_for('views_attendee.attendee_invites'))

@views_attendee.route('/reject_invite', methods=['POST'])
@login_required
def reject_invite():
    event_name_to_remove = request.form.get('event_name')
    reject_reason = request.form.get('reject_reason')

    # Find the Attendee's event invites
    attendee_event = Attendee_events6.query.filter_by(user_id=current_user.id).first()

    if attendee_event and attendee_event.invites:
        # Parse the JSON stored in the invites field
        invites = json.loads(attendee_event.invites)

        # Filter out the event to reject
        updated_invites = [event for event in invites if event['event_name'] != event_name_to_remove]

        # Save the rejection information
        rejected_invites = json.loads(attendee_event.rejected_invites or '[]')
        rejected_invites.append({
            'event_name': event_name_to_remove,
            'reject_reason': reject_reason,
            'attendee_name': current_user.first_name,
            'attendee_lname': current_user.last_name,
            'attendee_email': current_user.email
        })

        # Convert the updated invite list back to JSON format
        attendee_event.invites = json.dumps(updated_invites)
        attendee_event.rejected_invites = json.dumps(rejected_invites)

        # Commit the changes to the database
        db.session.commit()

    return redirect(url_for('views_attendee.attendee_invites'))

@views_attendee.route('/attendee_browse', methods=['GET', 'POST'])
def attendee_browse():
    # Fetch only public events
    public_events = Events11.query.filter_by(event_privacy="Public").all()
    events_data = []
    
    for event in public_events:
        # Get event creator's name from Users6 table
        creator = Users6.query.get(event.user_id)
        creator_name = f"{creator.first_name} {creator.last_name}" if creator else "Unknown"

        if event.data1:  # Check if data1 is not None
            event_data = json.loads(event.data1)
        else:
            event_data = {}  # Default to an empty dictionary if data1 is None

        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'creator_name': creator_name,
            'room_code': event.room_code,
            'start_date': event.start_date.strftime("%Y-%m-%d %H:%M"),
            'end_date': event.end_date.strftime("%Y-%m-%d %H:%M")
        })
    return render_template('attendee_browse.html', user=current_user, name=current_user.first_name, public_events=events_data)

@views_attendee.route('/attendee_events', methods=['GET', 'POST'])
@login_required
def attendee_events():
    attendee_event = Attendee_events6.query.filter_by(user_id=current_user.id).first()
    
    attending_events = []
    if attendee_event and attendee_event.rsvp_events:
        attending_events = json.loads(attendee_event.rsvp_events)
    
    return render_template('attendee_events.html', user=current_user, name=current_user.first_name, attending_events=attending_events)

@views_attendee.route('/attendee_history')
@login_required
def attendee_history():
    # Query all records where the current user is the attendee
    attendee_history = Attendee_records2.query.filter_by(attendee_id=current_user.id).all()

    return render_template('attendee_history.html', user=current_user, name=current_user.first_name, attendee_history=attendee_history)