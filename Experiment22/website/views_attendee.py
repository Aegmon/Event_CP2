from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Events8, Users2, Attendee_events5, Client_events4, Supplier_info, Event_records2, Attendee_records2
from . import db
from .gen_algo import *
import json
import csv
from datetime import datetime

views_attendee = Blueprint('views_attendee', __name__)

######################################################################################################################################################### Attendee
@views_attendee.route('/attendee', methods=['GET', 'POST'])
def attendee():
    return render_template('attendee.html', user=current_user, name=current_user.first_name)

@views_attendee.route('/attendee_invites', methods=['GET', 'POST'])
@login_required
def attendee_invites():

    # Get the invites stored in the Attendee_events5 table
    attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()
    
    invited_events = []
    if attendee_event and attendee_event.invites:
        invited_events = json.loads(attendee_event.invites)

    return render_template('attendee_invites.html', user=current_user, name=current_user.first_name, invited_events=invited_events)

@views_attendee.route('/accept_invite', methods=['POST'])
@login_required
def accept_invite():
    event_name = request.form.get('event_name')
    
    # Find the event in the Events8 table
    event = Events8.query.filter_by(event_name=event_name).first()
    
    if event:
        # Add this event to the current user's RSVP events in Attendee_events5
        attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()
        if attendee_event:
            rsvp_events = json.loads(attendee_event.rsvp_events) if attendee_event.rsvp_events else []
            rsvp_events.append({
                'event_name': event.event_name,
                'event_desc': event.event_desc,
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
            new_attendee_event = Attendee_events5(
                user_id=current_user.id,
                rsvp_events=json.dumps([{
                    'event_name': event.event_name,
                    'event_desc': event.event_desc,
                    'start_date': str(event.start_date),
                    'end_date': str(event.end_date),
                    'event_privacy': event.event_privacy
                }]),
                invites=json.dumps([])  # Initialize invites as empty if needed
            )
            db.session.add(new_attendee_event)

        # Add the user's details to the event's RSVP attendees in Events8
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
    attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()

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
    # Fetch all public events
    public_events = Events8.query.filter_by(event_privacy='Public').all()
    return render_template('attendee_browse.html', user=current_user, name=current_user.first_name, public_events=public_events)

@views_attendee.route('/attendee_events', methods=['GET', 'POST'])
@login_required
def attendee_events():
    attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()
    
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