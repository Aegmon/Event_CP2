from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Events8, Users2, Attendee_events5, Client_events4, Supplier_info, Event_records2, Attendee_records2
from . import db
from .gen_algo import *
import json
import csv
from datetime import datetime

views_client = Blueprint('views_client', __name__)

######################################################################################################################################################### Client

@views_client.route('/client', methods=['GET', 'POST'])
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

@views_client.route('/client_events', methods=['POST', 'GET'])
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

@views_client.route('/delete_supplier', methods=['POST'])
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

@views_client.route('/client_delete_event', methods=['POST'])
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

@views_client.route('/client_hire_supplier', methods=['POST', 'GET'])
def client_hire_supplier():
    return render_template("client_hire_supplier.html", user=current_user,  new_things=new_things, name=current_user.first_name, supplier_list1=supplier_list1)