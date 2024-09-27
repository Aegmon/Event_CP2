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
        return redirect(url_for('views.create_event_home'))
    elif current_user.role == "Client":
        return redirect(url_for('views.client'))
    elif current_user.role == "Attendee":
        return redirect(url_for('views.attendee'))
    elif current_user.role == "Supplier":
        return redirect(url_for('views.supplier'))
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
######################################################################################################################################################### Client

@views.route('/client', methods=['GET', 'POST'])
@login_required
def client():
    if request.method == 'POST':
        # Get form inputs
        event_name = request.form.get('event_name')
        event_desc = request.form.get('event_desc')
        event_type = request.form.get('event_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        budget = request.form.get('budget')
        max_attendee_num_str = request.form.get('max_attendee_num')

        # Check if any of the required fields are empty
        if not event_name or not event_desc or not start_date_str or not end_date_str or not budget or not max_attendee_num_str or not event_type:
            flash('Please fill out all fields.', category='error')
            return redirect(request.url)

        # Validate budget
        try:
            budget = int(budget)
            if budget < 5000:
                flash('Budget must be at least 5000 Pesos.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Budget must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)

        # Validate maximum attendees
        try:
            max_attendee_num = int(max_attendee_num_str)
            if max_attendee_num < 1:
                flash('Maximum Attendees must be at least 1.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Maximum Attendees must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)

        # Convert date strings to datetime objects
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Please provide valid start and end dates.', category='error')
            return redirect(request.url)

        # Validate that end date is not before start date
        if end_date < start_date:
            flash('End date cannot be before the start date.', category='error')
            return redirect(request.url)

        # Run your evolutionary algorithm
        weight_limit = budget
        fitness_limit = 500  # Adjust fitness limit to reflect more restrictive price limit
        population_size = 20  # Increase population size for better exploration
        generation_limit = 200  # Increase generation limit for thorough search

        population, generations = run_evolution(
            populate_func=partial(
                generate_population, size=population_size, genome_length=len(things_list)
            ),
            fitness_func=partial(
                fitness, things_list=things_list, weight_limit=weight_limit
            ),
            fitness_limit=fitness_limit,
            generation_limit=generation_limit
        )

        # Extract best answers from the result
        best_answers = genome_to_things(population[0], things_list)

        if len(best_answers) < 1:
            flash('Error', category='error')
        else:
            # Convert the list of best answers to JSON
            answers_json = json.dumps(best_answers)

            # Create new client event instance and save it to the database
            new_client_event = Client_events4(
                event_name=event_name,
                event_type=event_type,
                event_desc=event_desc,  # Save event description
                data1=answers_json,
                user_id=current_user.id,
                max_attendee_num=max_attendee_num,
                start_date=start_date,  # Saving start date
                end_date=end_date  # Saving end date
            )
            db.session.add(new_client_event)
            db.session.commit()  # Save the client event to the database

            flash('Client event added!', category='success')
    
    return render_template("client.html", user=current_user, new_things=new_things, name=current_user.first_name)

@views.route('/client_events', methods=['POST', 'GET'])
def client_events():
    user_events = current_user.client_events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)

        # Initialize arrays for suggested suppliers
        cake_thing = []
        caterer_thing = []
        balloons_thing = []
        photo_thing = []

        # Total weight calculation
        total_weight = sum(thing.price for thing in new_things if thing.name in event_data)

        # Check for matches in supplier lists and include rating and price
        for item in event_data:
            for supplier in cake1:
                if supplier.name == item:
                    cake_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in caterer1:
                if supplier.name == item:
                    caterer_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in balloons1:
                if supplier.name == item:
                    balloons_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in photographer1:
                if supplier.name == item:
                    photo_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})

        # Append event details, including suggested suppliers
        events_data.append({
            'event_name': event.event_name,
            'event_type': event.event_type,
            'event_desc': event.event_desc,
            'data1': event_data,
            'id': event.id,
            'total_weight': total_weight,
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'cake_thing': cake_thing,
            'caterer_thing': caterer_thing,
            'balloons_thing': balloons_thing,
            'photo_thing': photo_thing
        })

    return render_template("client_events.html", user=current_user, new_things=new_things, name=current_user.first_name, client_events=events_data)

@views.route('/delete_supplier', methods=['POST'])
@login_required
def delete_supplier():
    data = request.get_json()  # Get the JSON data from the request
    event_id = data.get('event_id')
    supplier_name = data.get('supplier_name')

    # Fetch the event by ID
    event = Client_events4.query.filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        return jsonify({'success': False, 'message': 'Event not found'}), 404

    # Load the current event data1 field (JSON stored in the database)
    event_data = json.loads(event.data1)

    # Remove the supplier from the event data if it exists
    if supplier_name in event_data:
        event_data.remove(supplier_name)

        # Update the event data1 field with the modified data
        event.data1 = json.dumps(event_data)
        db.session.commit()  # Save changes to the database

        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Supplier not found in event data'}), 400

@views.route('/client_delete_event', methods=['POST'])
@login_required
def client_delete_event():
    data = request.get_json()
    event_id = data.get('event_id')

    # Fetch the event by ID
    event = Client_events4.query.filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        return jsonify({'success': False, 'message': 'Event not found'}), 404

    # Delete the event from the database
    db.session.delete(event)
    db.session.commit()

    return jsonify({'success': True})

@views.route('/client_hire_supplier', methods=['POST', 'GET'])
def client_hire_supplier():
    return render_template("client_hire_supplier.html", user=current_user,  new_things=new_things, name=current_user.first_name, supplier_list1=supplier_list1)

######################################################################################################################################################### Attendee
@views.route('/attendee', methods=['GET', 'POST'])
def attendee():
    return render_template('attendee.html', user=current_user, name=current_user.first_name)

@views.route('/attendee_invites', methods=['GET', 'POST'])
@login_required
def attendee_invites():

    # Get the invites stored in the Attendee_events5 table
    attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()
    
    invited_events = []
    if attendee_event and attendee_event.invites:
        invited_events = json.loads(attendee_event.invites)

    return render_template('attendee_invites.html', user=current_user, name=current_user.first_name, invited_events=invited_events)

@views.route('/accept_invite', methods=['POST'])
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
    
    return redirect(url_for('views.attendee_invites'))

@views.route('/reject_invite', methods=['POST'])
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

    return redirect(url_for('views.attendee_invites'))

@views.route('/attendee_browse', methods=['GET', 'POST'])
def attendee_browse():
    # Fetch all public events
    public_events = Events8.query.filter_by(event_privacy='Public').all()
    return render_template('attendee_browse.html', user=current_user, name=current_user.first_name, public_events=public_events)

@views.route('/attendee_events', methods=['GET', 'POST'])
@login_required
def attendee_events():
    attendee_event = Attendee_events5.query.filter_by(user_id=current_user.id).first()
    
    attending_events = []
    if attendee_event and attendee_event.rsvp_events:
        attending_events = json.loads(attendee_event.rsvp_events)
    
    return render_template('attendee_events.html', user=current_user, name=current_user.first_name, attending_events=attending_events)

@views.route('/attendee_history')
@login_required
def attendee_history():
    # Query all records where the current user is the attendee
    attendee_history = Attendee_records2.query.filter_by(attendee_id=current_user.id).all()

    return render_template('attendee_history.html', user=current_user, name=current_user.first_name, attendee_history=attendee_history)

######################################################################################################################################################### Supplier

@views.route('/supplier', methods=['GET', 'POST'])
def supplier():
    # Check if the user already has supplier information
    supplier_info = Supplier_info.query.filter_by(user_id=current_user.id).first()

    if supplier_info:
        # If supplier information exists, render the profile page with all supplier data
        return render_template('supplier_prof.html', user=current_user, 
                               supplier_type=supplier_info.supplier_type,
                               av_commission=supplier_info.av_commission,
                               nickname=supplier_info.nickname,
                               phone_number=supplier_info.phone_number,
                               email_sup=supplier_info.email_sup,
                               self_desc=supplier_info.self_desc)
    else:
        # If no supplier information exists, handle the POST request or render the supplier form
        if request.method == 'POST':
            supplier_type = request.form.get('supplier_type')
            av_commission = request.form.get('av_commission')
            nickname = request.form.get('nickname')
            phone_number = request.form.get('phone_number')
            email_sup = request.form.get('email_sup')
            self_desc = request.form.get('self_desc')
            
            new_supplier = Supplier_info(
                supplier_type=supplier_type,
                av_commission=av_commission,
                nickname=nickname,
                phone_number=phone_number,
                email_sup=email_sup,
                self_desc=self_desc,
                user_id=current_user.id  # Associate the supplier with the current user
            )
            db.session.add(new_supplier)
            db.session.commit()

            # Prepare the data to append to the CSV file
            data_to_append = [nickname, "0", av_commission]

            # Open the CSV file in append mode
            with open(csv_file_path, 'a', newline='') as file:
                writer = csv.writer(file)
                # Append the new row
                writer.writerow(data_to_append)

            return render_template('supplier_prof.html', user=current_user, 
                                   supplier_type=supplier_type, 
                                   av_commission=av_commission, 
                                   nickname=nickname, 
                                   phone_number=phone_number, 
                                   email_sup=email_sup, 
                                   self_desc=self_desc)

        return render_template('supplier.html', user=current_user)



######################################################################################################################################################### Event Creator

@views.route('/create_event_home', methods=['GET', 'POST'])
@login_required
def create_event_home():
    return render_template('create_event_home.html', user=current_user, name=current_user.first_name)

@views.route('/create-event', methods=['GET', 'POST'])
@login_required
def event():
    if request.method == 'POST':
        # Get form inputs
        event_name = request.form.get('event_name')
        event_desc = request.form.get('event_desc')
        event_type = request.form.get('event_type')
        event_privacy = request.form.get('event_privacy')  # New input for event status
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        budget = request.form.get('budget')
        max_attendee_num_str = request.form.get('max_attendee_num')

        # Get selected attendees and their details
        selected_attendees = request.form.getlist('attendees')

        # Check if any of the required fields are empty
        if not event_name or not event_desc or not start_date_str or not end_date_str or not budget or not max_attendee_num_str:
            flash('Please fill out all fields.', category='error')
            return redirect(request.url)

        # Validate budget
        try:
            budget = int(budget)
            if budget < 5000:
                flash('Budget must be at least 5000 Pesos.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Budget must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)

        # Validate maximum attendees
        try:
            max_attendee_num = int(max_attendee_num_str)
            if max_attendee_num < 1:
                flash('Maximum Attendees must be at least 1.', category='error')
                return redirect(request.url)
        except ValueError:
            flash('Maximum Attendees must be a valid whole number (no decimals).', category='error')
            return redirect(request.url)

        # Convert date strings to datetime objects
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Please provide valid start and end dates.', category='error')
            return redirect(request.url)

        # Ensure the end date is after the start date
        if end_date < start_date:
            flash('End date cannot be before start date.', category='error')
            return redirect(request.url)

        # Fetch attendee details from the database based on the selected IDs
        attendee_details = []
        for attendee_id in selected_attendees:
            attendee = Users2.query.get(attendee_id)
            if attendee:
                attendee_details.append({
                    'id': attendee.id,
                    'name': attendee.first_name,
                    'lname': attendee.last_name,
                    'email': attendee.email
                })

        # Convert selected attendee details to JSON
        invited_attendees_json = json.dumps(attendee_details)

        # Run your evolutionary algorithm (assuming other parts of the algorithm are implemented)
        weight_limit = budget
        fitness_limit = 500
        population_size = 20
        generation_limit = 200

        population, generations = run_evolution(
            populate_func=partial(generate_population, size=population_size, genome_length=len(things_list)),
            fitness_func=partial(fitness, things_list=things_list, weight_limit=weight_limit),
            fitness_limit=fitness_limit,
            generation_limit=generation_limit
        )

        best_answers = genome_to_things(population[0], things_list)

        if len(best_answers) < 1:
            flash('Error', category='error')
        else:
            # Convert the list of best answers to JSON
            answers_json = json.dumps(best_answers)

        # Create new event instance and save it to the database
        new_event = Events8(
            event_name=event_name,
            event_desc=event_desc,
            event_type=event_type,
            event_privacy=event_privacy,  # Save event status
            data1=answers_json,
            user_id=current_user.id,
            max_attendee_num=max_attendee_num,
            start_date=start_date,
            end_date=end_date,
            invited_attendees=invited_attendees_json  # Save the selected attendees as JSON
        )
        db.session.add(new_event)
        db.session.commit()

                # Save the event to Event_records2 as well
        new_event_record = Event_records2(
            event_name=event_name,
            event_desc=event_desc,
            event_type=event_type,
            event_privacy=event_privacy,
            start_date=start_date,
            end_date=end_date,
            creator_id=current_user.id  # Save the creator's user ID
        )
        db.session.add(new_event_record)

        db.session.commit()

        flash('Event added!', category='success')
    # Now store this event in each selected attendee's Attendee_events5 "invites" field
        for attendee_id in selected_attendees:
            attendee = Users2.query.get(attendee_id)
            if attendee:
                # Get or create the Attendee_events5 entry for this user
                attendee_event = Attendee_events5.query.filter_by(user_id=attendee.id).first()
                if not attendee_event:
                    attendee_event = Attendee_events5(user_id=attendee.id, invites='[]')
                    db.session.add(attendee_event)
                
                # Load the current invites
                invites = json.loads(attendee_event.invites)

                # Add the new event to the invites list
                invites.append({
                    'event_name': event_name,
                    'event_desc': event_desc,
                    'event_privacy': event_privacy,
                    'start_date': start_date.strftime('%Y-%m-%d %H:%M'),
                    'end_date': end_date.strftime('%Y-%m-%d %H:%M')
                })

                # Save back the updated invites list
                attendee_event.invites = json.dumps(invites)

        db.session.commit()

        flash('Event added and invites sent!', category='success')

    # Query all attendees with the role 'Attendee'
    attendees = Users2.query.filter_by(role='Attendee').all()

    return render_template("create-event.html", user=current_user, name=current_user.first_name, attendees=attendees)

@views.route('/created_event_edit', methods=['GET', 'POST'])
@login_required
def created_event_edit():
    # Fetch and display the user's existing events
    user_events = current_user.events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)

        cake_thing = []
        caterer_thing = []
        balloons_thing = []
        photo_thing = []

        for item in event_data:
            for supplier in cake1:
                if supplier.name == item:
                    cake_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in caterer1:
                if supplier.name == item:
                    caterer_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in balloons1:
                if supplier.name == item:
                    balloons_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in photographer1:
                if supplier.name == item:
                    photo_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})

        attendee_data = json.loads(event.invited_attendees)
        
        # Calculate total weight from the suppliers' arrays
        total_weight = (
            sum(supplier['price'] for supplier in cake_thing) +
            sum(supplier['price'] for supplier in caterer_thing) +
            sum(supplier['price'] for supplier in balloons_thing) +
            sum(supplier['price'] for supplier in photo_thing)
        )
        
        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'event_type': event.event_type,
            'event_privacy': event.event_privacy,
            'data1': event_data,
            'id': event.id,
            'total_weight': total_weight,
            'rsvp_attendees': event.rsvp_attendees,
            'invited_attendees': attendee_data,
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'cake_thing': cake_thing,
            'caterer_thing': caterer_thing,
            'balloons_thing': balloons_thing,
            'photo_thing': photo_thing
        })
    return render_template('create_event_edit.html', user=current_user, name=current_user.first_name, events=events_data, cake1=cake1, caterer1=caterer1, balloons1=balloons1, photographer1=photographer1)

@views.route('/add_supplier_to_event/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def add_supplier_to_event(event_id, supplier_name):
    event = Events8.query.get(event_id)

    if not event:
        return jsonify({'success': False, 'message': 'Event not found.'})

    # Load existing data1
    event_data = json.loads(event.data1)

    # Check which supplier category to add the supplier to (assumes supplier_name matches the category)
    supplier_type = None
    for supplier in cake1:
        if supplier.name == supplier_name:
            supplier_type = 'cake_thing'
            break
    for supplier in caterer1:
        if supplier.name == supplier_name:
            supplier_type = 'caterer_thing'
            break
    for supplier in balloons1:
        if supplier.name == supplier_name:
            supplier_type = 'balloons_thing'
            break
    for supplier in photographer1:
        if supplier.name == supplier_name:
            supplier_type = 'photo_thing'
            break

    if supplier_type:
        # Check if the supplier is already in the event data
        if supplier_name in event_data:
            return jsonify({'success': False, 'message': 'Supplier already added to the event.'})

        # Append supplier name to the event data
        event_data.append(supplier_name)  # Assuming you want to append the supplier name to data1
        event.data1 = json.dumps(event_data)  # Convert back to JSON
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Supplier not found.'})

@views.route('/creator_delete_supplier/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def creator_delete_supplier(event_id, supplier_name):
    # Fetch the event by ID
    event = Events8.query.filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        return jsonify({'success': False, 'message': 'Event not found'}), 404

    # Load the current event data1 field (JSON stored in the database)
    event_data = json.loads(event.data1)

    # Remove the supplier from the event data if it exists
    if supplier_name in event_data:
        event_data.remove(supplier_name)

        # Update the event data1 field with the modified data
        event.data1 = json.dumps(event_data)
        db.session.commit()  # Save changes to the database

        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Supplier not found in event data'}), 400

@views.route('/delete_event_created/<int:event_id>', methods=['POST'])
@login_required
def delete_event_created(event_id):
    # Find the event by its ID
    event = Events8.query.get(event_id)

    if event and event.user_id == current_user.id:
        # If the event exists and belongs to the current user, delete it
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', category='success')
    else:
        flash('Event not found or you do not have permission to delete it.', category='error')

    return redirect(url_for('views.event'))

@views.route('/event_attendee_list', methods=['GET', 'POST'])
@login_required
def event_attendee_list():
    user_events = current_user.events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)
        
        # Ensure invited_attendees is parsed as JSON, assuming it's stored as a string in the database.
        attendee_data = json.loads(event.invited_attendees) if isinstance(event.invited_attendees, str) else event.invited_attendees

        total_weight = sum(thing.price for thing in new_things if thing.name in event_data)
        
        # Parse the rsvp_attendees field if it's stored as JSON
        rsvp_attendees = json.loads(event.rsvp_attendees) if event.rsvp_attendees else []
        
        # Load rejected invites for this event
        rejected_invites = []
        for attendee in attendee_data:
            # Make sure that each attendee is treated as a dictionary
            if isinstance(attendee, dict) and 'id' in attendee:
                attendee_event = Attendee_events5.query.filter_by(user_id=attendee['id']).first()
                if attendee_event and attendee_event.rejected_invites:
                    rejected_invites_json = json.loads(attendee_event.rejected_invites)
                    # Filter for this specific event's rejected invites
                    rejected_for_event = [reject for reject in rejected_invites_json if reject['event_name'] == event.event_name]
                    rejected_invites.extend(rejected_for_event)
            else:
                print(f"Unexpected attendee data structure: {attendee}")

        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'data1': event_data,
            'id': event.id,
            'total_weight': total_weight,
            'rsvp_attendees': rsvp_attendees,  # Decoded RSVP attendees
            'invited_attendees': attendee_data,
            'rejected_invites': rejected_invites,  # Add rejected invite details
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date
        })

    return render_template('event_attendee_list.html', user=current_user, name=current_user.first_name, events=events_data)

@views.route('/create_event_history')
@login_required
def create_event_history():
    # Query all records created by the current user
    event_history = Event_records2.query.filter_by(creator_id=current_user.id).all()

    return render_template('create_event_history.html', user=current_user, name=current_user.first_name, event_history=event_history)

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
