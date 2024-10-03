from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Events11, Users6, Attendee_events6, Client_events4, Supplier_info6, Event_records2, Attendee_records2
from . import db
from .gen_algo_final import *
import json
import csv
from datetime import datetime

views_client = Blueprint('views_client', __name__)


@views_client.route('/create_event_profile_client')
@login_required
def create_event_profile():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
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
            if budget < 20000:
                flash('Budget must be at least 20000 Pesos.', category='error')
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

        # Run Algo Here
        total_price = sum(thing.price for thing in things_list)
        max_price_limit = float(budget)  # Set to your desired maximum price
        price_limit = min(total_price, max_price_limit)

        fitness_limit = 1000
        population_size = 20
        generation_limit = 100  

        best_genome, generations = run_evolution(
        populate_func=partial(generate_population, size=population_size),
        fitness_func=partial(fitness, price_limit=price_limit),
        fitness_limit=fitness_limit,
        generation_limit=generation_limit
        )

        best_answers = genome_to_things(best_genome, price_limit)

        # Convert the list of best answers to JSON
        answers_json = json.dumps(best_answers)

        # Create new event instance and save it to the database
        new_event = Client_events4(
            event_name=event_name,
            event_desc=event_desc,
            event_type=event_type,  # Save event status
            data1=answers_json,
            user_id=current_user.id,
            max_attendee_num=max_attendee_num,
            start_date=start_date,
            end_date=end_date,  # Save the selected attendees as JSON
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Client event added!', category='success')
    
    return render_template("client.html", user=current_user, new_things=new_things, name=current_user.first_name)

@views_client.route('/client_events', methods=['POST', 'GET'])
def client_events():
    user_events = current_user.client_events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)

        cake_thing = []
        digital_printing_thing = []
        event_planner_thing = []
        grazing_table_thing = []
        makeup_and_hair_thing = []
        photobooth_thing = []
        photographer_thing = []
        catering_thing = [] 
        church_thing = []
        event_stylist_thing = []
        events_place_thing = []
        lights_and_sounds_thing = []

        for item in event_data:
            for supplier in cake1:
                if supplier.name == item:
                    cake_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in digital_printing1:
                if supplier.name == item:
                    digital_printing_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in event_planner1:
                if supplier.name == item:
                    event_planner_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in grazing_table1:
                if supplier.name == item:
                    grazing_table_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in makeup_and_hair1:
                if supplier.name == item:
                    makeup_and_hair_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in photobooth1:
                if supplier.name == item:
                    photobooth_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in photographer1:
                if supplier.name == item:
                    photographer_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in catering1:
                if supplier.name == item:
                    catering_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in church1:
                if supplier.name == item:
                    church_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in event_stylist1:
                if supplier.name == item:
                    event_stylist_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in events_place1:
                if supplier.name == item:
                    events_place_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
            for supplier in lights_and_sounds1:
                if supplier.name == item:
                    lights_and_sounds_thing.append({'name': supplier.name, 'price': supplier.price, 'rating': supplier.rating})
        
        # Calculate total weight from the suppliers' arrays
        total_price = (
            sum(supplier['price'] for supplier in cake_thing) +
            sum(supplier['price'] for supplier in digital_printing_thing ) +
            sum(supplier['price'] for supplier in event_planner_thing ) +
            sum(supplier['price'] for supplier in grazing_table_thing ) +
            sum(supplier['price'] for supplier in makeup_and_hair_thing ) +
            sum(supplier['price'] for supplier in photobooth_thing ) +
            sum(supplier['price'] for supplier in photographer_thing ) +
            sum(supplier['price'] for supplier in catering_thing ) +
            sum(supplier['price'] for supplier in church_thing ) +
            sum(supplier['price'] for supplier in event_stylist_thing ) +
            sum(supplier['price'] for supplier in events_place_thing  ) +
            sum(supplier['price'] for supplier in lights_and_sounds_thing )
        )
        
        events_data.append({
            'event_name': event.event_name,
            'event_desc': event.event_desc,
            'event_type': event.event_type,
            'data1': event_data,
            'id': event.id,
            'total_price': total_price,
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'cake_thing': cake_thing,
            'digital_printing_thing': digital_printing_thing,
            'event_planner_thing': event_planner_thing,
            'grazing_table_thing': grazing_table_thing,
            'makeup_and_hair_thing': makeup_and_hair_thing,
            'photobooth_thing': photobooth_thing,
            'photographer_thing': photographer_thing,
            'catering_thing': catering_thing,
            'church_thing': church_thing,
            'event_stylist_thing': event_stylist_thing,
            'events_place_thing': events_place_thing,
            'lights_and_sounds_thing': lights_and_sounds_thing

        })

    return render_template("client_events.html", user=current_user, name=current_user.first_name, client_events=events_data, cake1=cake1, 
                                                    digital_printing1=digital_printing1, event_planner1=event_planner1, 
                                                    grazing_table1=grazing_table1, makeup_and_hair1=makeup_and_hair1, 
                                                    photobooth1=photobooth1, photographer1=photographer1, catering1=catering1, 
                                                    church1=church1, event_stylist1=event_stylist1, events_place1=events_place1, 
                                                    lights_and_sounds1=lights_and_sounds1)

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
    return render_template("client_hire_supplier.html", user=current_user,  new_things=new_things, name=current_user.first_name, things_list=things_list)