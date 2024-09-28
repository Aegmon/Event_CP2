from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Events8, Users2, Attendee_events5, Client_events4, Supplier_info, Event_records2, Attendee_records2
from . import db
from .gen_algo import *
import json
import csv
from datetime import datetime

views = Blueprint('views', __name__)
csv_file_path = 'C:/Users/Adrian/Desktop/HTML Guide 2/Capstone/Experiment1/website/things.csv'

######################################################################################################################################################### Home

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')  # Gets the note from the HTML

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)  # providing the schema for the note 
            db.session.add(new_note)  # adding the note to the database
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)  # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    return jsonify({})

######################################################################################################################################################### Role Redirection And Calendar

@views.route('/role', methods=['GET', 'POST'])
def role():
    if current_user.role == "Event Creator":
        return redirect(url_for('views_creator.create_event_home'))
    elif current_user.role == "Client":
        return redirect(url_for('views_client.client'))
    elif current_user.role == "Attendee":
        return redirect(url_for('views_attendee.attendee'))
    elif current_user.role == "Supplier":
        return redirect(url_for('views_supplier.supplier'))
    else:
        return render_template("home.html", user=current_user)
    
@views.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html', user = current_user)

@views.route('/fetch-events')
@login_required
def fetch_events():
    # Fetch events created by the user
    user_events = current_user.events
    events = []

    # Add created events to the calendar
    for event in user_events:
        events.append({
            'title': event.event_name,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat(),
        })

    # Fetch the user's RSVP events from Attendee_events5
    attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()
    if attendee_event and attendee_event.rsvp_events:
        rsvp_events = json.loads(attendee_event.rsvp_events)
        for rsvp_event in rsvp_events:
            events.append({
                'title': rsvp_event['event_name'],
                'start': rsvp_event['start_date'],
                'end': rsvp_event['end_date'],
                'description': rsvp_event['event_desc'],  # Add description if needed
                'event_privacy': rsvp_event['event_privacy'],  # Include privacy status if needed
            })

    return jsonify(events)

######################################################################################################################################################### Events List

@views.route('/event_list', methods=['GET'])
def event_list():
    # Fetch all events
    all_events = Events8.query.all()
    events_data = []
    for event in all_events:
        if event.data1:  # Check if data1 is not None
            event_data = json.loads(event.data1)
        else:
            event_data = {}  # Default to an empty dictionary if data1 is None
        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'event_type': event.event_type,
            'id': event.id,
            'start_date': event.start_date.strftime("%Y-%m-%d %H:%M"),
            'end_date': event.end_date.strftime("%Y-%m-%d %H:%M")
        })

    return render_template("events_list.html", user=current_user, events=events_data)
