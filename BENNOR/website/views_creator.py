from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from .models import Note, Events15, Users7, Attendee_events7, Client_events6, Supplier_info8, Event_records4, Attendee_records3, Supplier_Req_Jobs3, SupplierJobs3, HiredSuppliers3, Client_Hired_Suppliers3
from . import db, socketio
from .gen_algo_final import *
import json, random, csv
from flask_socketio import join_room, leave_room, send, SocketIO, emit
from datetime import datetime
from string import ascii_uppercase

views_creator = Blueprint('views_creator', __name__)

rooms = {}

@views_creator.route('/create_event_profile')
@login_required
def create_event_profile():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
########################################################################################################################################################################### Event Creator Video Chat

@views_creator.route("/video_chat_dashboard", methods=["POST", "GET"])
@login_required
def video_chat_dashboard():
    return render_template("video_chat_dashboard.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

@views_creator.route("/video_create_meeting", methods=["POST", "GET"])
@login_required
def video_create_meeting():
    return render_template("video_create_meeting.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

@views_creator.route("/video_join_meeting", methods=["POST", "GET"])
@login_required
def video_join_meeting():
    if request.method == "POST":
        room_id = request.form.get("roomID")
        return redirect(f"/video_create_meeting?roomID={room_id}")
    return render_template("video_join_meeting.html", user=current_user, role=current_user.role, first_name=current_user.first_name, last_name=current_user.last_name)

########################################################################################################################################################################### Event Creater Live Chat
def generate_unique_code(length=5):
    """Generates a unique room code."""
    while True:
        code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            rooms[code] = {"messages": [], "members": 0}  # Initialize room structure
            return code

@views_creator.route("/join_room", methods=["POST", "GET"])
@login_required
def join_room_view():
    """Page where users enter the room code to join."""
    session.clear()
    events = Events15.query.all()  # Query all events

    if request.method == "POST":
        code = request.form.get("code")
        if not code:
            return render_template("join_room.html", error="Please enter a room code.", user=current_user, role=current_user.role, events=events)

        if code not in rooms:
            return render_template("join_room.html", error="Room does not exist.", user=current_user, role=current_user.role, events=events)

        session["room"] = code
        session["name"] = current_user.role + " : " + current_user.first_name  # Use the user's first name
        return redirect(url_for('views_creator.room'))

    return render_template("join_room.html", user=current_user, role=current_user.role, events=events)

@views_creator.route("/room")
@login_required
def room():
    """Chat room view."""
    room_code = session.get("room")
    if room_code is None or room_code not in rooms:
        return redirect(url_for("views_creator.join_room_view"))
    
    # Retrieve the event associated with this room code
    event = Events15.query.filter_by(room_code=room_code).first()
    if not event:
        flash("No event found for this room.")
        return redirect(url_for("views_creator.join_room_view"))
    
    event_name = event.event_name  # Get the event name
    creator = Users7.query.filter_by(id=event.user_id).first()  # Get event creator's name
    creator_name = f"{creator.first_name} {creator.last_name}"

    return render_template("room.html", user=current_user, code=room_code, event_name=event_name, creator_name=creator_name, messages=rooms[room_code]["messages"], role=current_user.role)

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

########################################################################################################################################################################### Event Creator Home

@views_creator.route('/create_event_home', methods=['GET', 'POST'])
@login_required
def create_event_home():
    return render_template('create_event_home.html', user=current_user, name=current_user.first_name)

@views_creator.route('/view_hired_suppliers', methods=['GET'])
@login_required
def view_hired_suppliers():
    # Fetch all hired suppliers that belong to the current user
    hired_suppliers = HiredSuppliers3.query.filter_by(user_id=current_user.id).all()

    # Pass the list of hired suppliers to the template
    return render_template('view_hired_suppliers.html', hired_suppliers=hired_suppliers, user=current_user)

########################################################################################################################################################################### Event Creator Create
########################################################################################################################################################################### Event Creator Create

@views_creator.route('/create-event', methods=['GET', 'POST'])
@login_required
def event():
    if request.method == 'POST':
        # Get form inputs
        event_name = request.form.get('event_name')
        event_desc = request.form.get('event_desc')
        event_type = request.form.get('event_type')
        event_privacy = request.form.get('event_privacy')  # New input for event status
        budget = request.form.get('budget')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        max_attendee_num_str = request.form.get('max_attendee_num')
        selected_attendees = request.form.getlist('attendees')

        # Generate a unique room code for the chat room
        room_code = generate_unique_code()
        session["room"] = room_code
        session["name"] = current_user.role + " : " + current_user.first_name  # Or however you want to set the name

        # Save the room to persist chats
        rooms[room_code] = {"members": 0, "messages": []}

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
        # Ensure the end date is after the start date
        if end_date < start_date:
            flash('End date cannot be before start date.', category='error')
            return redirect(request.url)

        # Fetch attendee details from the database based on the selected IDs
        attendee_details = []
        for attendee_id in selected_attendees:
            attendee = Users7.query.get(attendee_id)
            if attendee:
                attendee_details.append({
                    'id': attendee.id,
                    'name': attendee.first_name,
                    'lname': attendee.last_name,
                    'email': attendee.email
                })

        # Convert selected attendee details to JSON
        invited_attendees_json = json.dumps(attendee_details)

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
        new_event = Events15(
            event_name=event_name,
            event_desc=event_desc,
            room_code=room_code,
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

        flash('Event added!', category='success')
        # Now store this event in each selected attendee's Attendee_events7 "invites" field
        for attendee_id in selected_attendees:
            attendee = Users7.query.get(attendee_id)
            if attendee:
                # Get or create the Attendee_events7 entry for this user
                attendee_event = Attendee_events7.query.filter_by(user_id=attendee.id).first()
                if not attendee_event:
                    attendee_event = Attendee_events7(user_id=attendee.id, invites='[]')
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
    attendees = Users7.query.filter_by(role='Attendee').all()

    return render_template("create-event.html", user=current_user, name=current_user.first_name, attendees=attendees)

###########################################################################################################################################################################

@views_creator.route('/created_event_edit', methods=['GET', 'POST'])
@login_required
def created_event_edit():
    # Fetch and display the user's existing events
    user_events = current_user.events
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

        attendee_data = json.loads(event.invited_attendees)
        
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
            'room_code': event.room_code,
            'event_desc': event.event_desc,
            'event_type': event.event_type,
            'event_privacy': event.event_privacy,
            'data1': event_data,
            'id': event.id,
            'total_price': total_price,
            'rsvp_attendees': event.rsvp_attendees,
            'invited_attendees': attendee_data,
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
    return render_template('create_event_edit.html', user=current_user, name=current_user.first_name, events=events_data, cake1=cake1, 
                                                    digital_printing1=digital_printing1, event_planner1=event_planner1, 
                                                    grazing_table1=grazing_table1, makeup_and_hair1=makeup_and_hair1, 
                                                    photobooth1=photobooth1, photographer1=photographer1, catering1=catering1, 
                                                    church1=church1, event_stylist1=event_stylist1, events_place1=events_place1, 
                                                    lights_and_sounds1=lights_and_sounds1, supplier_others=supplier_others)

###########################################################################################################################################################################

@views_creator.route('/add_supplier_to_event/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def add_supplier_to_event(event_id, supplier_name):
    event = Events15.query.get(event_id)

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
    for supplier in digital_printing1:
        if supplier.name == supplier_name:
            supplier_type = 'digital_printing_thing'
            break
    for supplier in event_planner1:
        if supplier.name == supplier_name:
            supplier_type = 'event_planner_thing'
            break
    for supplier in grazing_table1:
        if supplier.name == supplier_name:
            supplier_type = 'grazing_table_thing'
            break
    for supplier in makeup_and_hair1:
        if supplier.name == supplier_name:
            supplier_type = 'makeup_and_hair_thing'
            break
    for supplier in photobooth1:
        if supplier.name == supplier_name:
            supplier_type = 'photobooth_thing'
            break
    for supplier in photographer1:
        if supplier.name == supplier_name:
            supplier_type = 'photographer_thing'
            break
    for supplier in catering1:
        if supplier.name == supplier_name:
            supplier_type = 'catering_thing'
            break
    for supplier in church1:
        if supplier.name == supplier_name:
            supplier_type = 'church_thing'
            break
    for supplier in event_stylist1:
        if supplier.name == supplier_name:
            supplier_type = 'event_stylist_thing'
            break
    for supplier in events_place1:
        if supplier.name == supplier_name:
            supplier_type = 'events_place_thing'
            break
    for supplier in lights_and_sounds1:
        if supplier.name == supplier_name:
            supplier_type = 'lights_and_sounds_thing'
            break
    for supplier in supplier_others:
        if supplier.name == supplier_name:
            supplier_type = 'others'
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

###########################################################################################################################################################################

@views_creator.route('/creator_delete_supplier/<int:event_id>/<string:supplier_name>', methods=['POST'])
@login_required
def creator_delete_supplier(event_id, supplier_name):
    # Fetch the event by ID
    event = Events15.query.filter_by(id=event_id, user_id=current_user.id).first()

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

###########################################################################################################################################################################

@views_creator.route('/delete_event_created/<int:event_id>', methods=['POST'])
@login_required
def delete_event_created(event_id):
    # Find the event by its ID
    event = Events15.query.get(event_id)

    if event and event.user_id == current_user.id:
        # If the event exists and belongs to the current user, delete it
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', category='success')
    else:
        flash('Event not found or you do not have permission to delete it.', category='error')

    return redirect(url_for('views_creator.event'))

###########################################################################################################################################################################

@views_creator.route('/event_attendee_list', methods=['GET', 'POST'])
@login_required
def event_attendee_list():
    user_events = current_user.events
    events_data = []

    for event in user_events:
        event_data = json.loads(event.data1)
        
        # Ensure invited_attendees is parsed as JSON, assuming it's stored as a string in the database.
        attendee_data = json.loads(event.invited_attendees) if isinstance(event.invited_attendees, str) else event.invited_attendees

        # total_price = sum(thing.price for thing in new_things if thing.name in event_data)
        
        # Parse the rsvp_attendees field if it's stored as JSON
        rsvp_attendees = json.loads(event.rsvp_attendees) if event.rsvp_attendees else []
        
        # Load rejected invites for this event
        rejected_invites = []
        for attendee in attendee_data:
            # Make sure that each attendee is treated as a dictionary
            if isinstance(attendee, dict) and 'id' in attendee:
                attendee_event = Attendee_events7.query.filter_by(user_id=attendee['id']).first()
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
            'rsvp_attendees': rsvp_attendees,  # Decoded RSVP attendees
            'invited_attendees': attendee_data,
            'rejected_invites': rejected_invites,  # Add rejected invite details
            'max_attendee_num': event.max_attendee_num,
            'start_date': event.start_date,
            'end_date': event.end_date
        })

    return render_template('event_attendee_list.html', user=current_user, name=current_user.first_name, events=events_data)

###########################################################################################################################################################################

@views_creator.route('/create_event_history', methods=['GET', 'POST'])
@login_required
def create_event_history():
    # Fetch all event records created by the current user
    event_history = Event_records4.query.filter_by(creator_id=current_user.id).all()

    # Parse the JSON field (data1) for each event
    for event in event_history:
        if event.data1:
            try:
                event.supplier_names = json.loads(event.data1)  # Store the parsed names into a new attribute
            except json.JSONDecodeError:
                event.supplier_names = []  # If there's an issue with the JSON, set to an empty list
        else:
            event.supplier_names = []

    return render_template('create_event_history.html', user=current_user, event_history=event_history, name=current_user.first_name)

###########################################################################################################################################################################

@views_creator.route('/create_view_supplier/<string:supplier_name>', methods=['GET', 'POST'])
@login_required
def create_view_supplier(supplier_name):
    # Fetch supplier data from the database based on the fullname
    supplier_info = Supplier_info8.query.filter_by(fullname=supplier_name).first()

    # Check if supplier exists
    if not supplier_info:
        flash('Supplier not found!', 'danger')
        return redirect(url_for('views_creator.created_event_edit'))

    if request.method == 'POST':
        # Fetch data from the form
        supplier_id = request.form.get('supplier_id')  # Supplier ID to identify the supplier
        rating = float(request.form.get('rating'))  # Convert rating to float
        feedback = request.form.get('feedback')
        
        # Fetch the supplier from the database by ID
        supplier = Supplier_info8.query.get(supplier_id)
        if not supplier:
            flash('Supplier not found.', category='error')
            return redirect(request.url)

        # Calculate new overall rating (average of previous and new rating)
        if supplier.over_all_rating:
            previous_rating = float(supplier.over_all_rating)
            new_overall_rating = (previous_rating + rating) / 2
        else:
            new_overall_rating = rating  # If no previous rating, use the new rating

        supplier.rating = str(rating)  # Store rating as string
        supplier.feedback = feedback
        supplier.reviewer = f"{current_user.first_name} {current_user.last_name}"
        supplier.over_all_rating = str(new_overall_rating)  # Update the overall rating

        try:
            db.session.commit()  # Commit the changes to the database
            flash(f'Rating and feedback submitted for {supplier.fullname}.', category='success')
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            flash(f'Error submitting rating: {e}', category='error')

        return redirect(request.url)

    # Render the supplier_view.html template with supplier information
    return render_template('supplier_view.html', user=current_user, supplier=supplier_info, supplier_id=supplier_info.user_id)

###########################################################################################################################################################################

@views_creator.route('/create_rate_supplier', methods=['GET', 'POST'])
@login_required
def create_rate_supplier():
    suppliers = Supplier_info8.query.all()  # Fetch all suppliers from the database

    if request.method == 'POST':
        # Fetch data from the form
        supplier_id = request.form.get('supplier_id')  # Supplier ID to identify the supplier
        rating = float(request.form.get('rating'))  # Convert rating to float
        feedback = request.form.get('feedback')
        
        # Fetch the supplier from the database by ID
        supplier = Supplier_info8.query.get(supplier_id)
        if not supplier:
            flash('Supplier not found.', category='error')
            return redirect(request.url)

        # Calculate new overall rating (average of previous and new rating)
        if supplier.over_all_rating:
            previous_rating = float(supplier.over_all_rating)
            new_overall_rating = (previous_rating + rating) / 2
        else:
            new_overall_rating = rating  # If no previous rating, use the new rating

        # Update supplier's rating, feedback, and reviewer
        supplier.rating = str(rating)  # Store rating as string
        supplier.feedback = feedback
        supplier.reviewer = f"{current_user.first_name} {current_user.last_name}"
        supplier.over_all_rating = str(new_overall_rating)  # Update the overall rating

        try:
            db.session.commit()  # Commit the changes to the database
            flash(f'Rating and feedback submitted for {supplier.fullname}.', category='success')
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            flash(f'Error submitting rating: {e}', category='error')

        return redirect(request.url)

    return render_template('create_rate_supplier.html', user=current_user, suppliers=suppliers)

###########################################################################################################################################################################

@views_creator.route('/create_record/<int:event_id>', methods=['POST'])
@login_required
def create_record(event_id):
    # Fetch the specific event by ID
    event = Events15.query.get(event_id)
    
    if not event:
        flash('Event not found', category='error')
        return redirect(url_for('views_creator.create_event_edit'))

    # Check if the event has already been finalized (exists in Event_records4)
    existing_record = Event_records4.query.filter_by(creator_id=current_user.id, event_name=event.event_name).first()

    if existing_record:
        flash('This event has already been finalized and saved to history.', category='warning')
        return redirect(url_for('views_creator.create_event_edit'))

    # Extract event details
    event_name = event.event_name
    event_desc = event.event_desc
    event_type = event.event_type
    event_privacy = event.event_privacy
    start_date = event.start_date
    end_date = event.end_date
    room_code = event.room_code
    data1 = event.data1  # Assuming this contains a JSON string of supplier names

    # Create a new Event_records4 entry
    new_event_record = Event_records4(
        event_name=event_name,
        event_desc=event_desc,
        event_type=event_type,
        event_privacy=event_privacy,
        data1=data1,
        room_code=room_code,
        creator_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    try:
        # Add the new record to the database
        db.session.add(new_event_record)
        db.session.commit()
        flash('Event has been successfully saved to history!', category='success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving event: {e}", category='error')

    # Redirect to the event history page
    return redirect(url_for('views_creator.create_event_history'))

###########################################################################################################################################################################

@views_creator.route('/create_hire_supplier', methods=['POST'])
@login_required
def create_hire_supplier():
    supplier_name = request.form.get('supplier_name')
    event_id = request.form.get('event_id')
    
    # Fetch the specific event from Event_records4 by ID
    event = Event_records4.query.get(event_id)
    
    print(f"Attempting to hire supplier for event ID: {event_id}")  # Debugging line
    
    if not event:
        print("Event not found in the database.")  # Additional debug message
        flash('Event not found', category='error')
        return redirect(url_for('views_creator.create_event_history'))

    # Find the supplier by their full name
    supplier = Supplier_info8.query.filter_by(fullname=supplier_name).first()

    if not supplier:
        flash('Supplier not found', category='error')
        return redirect(url_for('views_creator.create_event_history'))

    # Create a new hire request in the Supplier_Req_Jobs3 table
    new_request = Supplier_Req_Jobs3(
        supplier_id=supplier.id,
        req_event_creator=current_user.first_name + ' ' + current_user.last_name,
        req_event_name=event.event_name,
        req_event_type=event.event_type,
        req_room_code=event.room_code,
        req_start_date=event.start_date,
        req_end_date=event.end_date
    )

    try:
        # Add and commit the new request to the database
        db.session.add(new_request)
        db.session.commit()
        flash('Supplier has been successfully hired!', category='success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error hiring supplier: {e}", category='error')

    return redirect(url_for('views_creator.create_event_history'))


########################################################################################################################################################################### Supplier
########################################################################################################################################################################### Supplier
supplier_others = []

@views_creator.route('/create_event_profile_supplier')
@login_required
def create_event_profile_supplier():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
########################################################################################################################################################################### Supplier

@views_creator.route('/supplier', methods=['GET', 'POST'])
@login_required
def supplier():
    # Check if the user already has supplier information
    supplier_info8 = Supplier_info8.query.filter_by(user_id=current_user.id).first()

    # If the supplier information exists, redirect to supplier profile page
    if supplier_info8:
        # requests = json.loads(supplier_info8.requests)
        return render_template('supplier_prof.html', 
                               user=current_user,
                               fullname=supplier_info8.fullname,
                               supplier_type=supplier_info8.supplier_type,
                               commission=supplier_info8.commission,
                               phone_number=supplier_info8.phone_number,
                               phone_number2=supplier_info8.phone_number2,
                               email_sup=supplier_info8.email_sup,
                               self_desc=supplier_info8.supplier_description,
                               extra_info=supplier_info8.extra_info,
                               rating=supplier_info8.rating)  # Use supplier_info8 rating

    # If supplier information doesn't exist, handle new entry
    if request.method == 'POST':
        fullname = current_user.first_name + " " + current_user.last_name
        supplier_type = request.form.get('supplier_type')
        commission = request.form.get('commission')
        phone_number = request.form.get('phone_number')
        phone_number2 = request.form.get('phone_number2')
        email_sup = request.form.get('email_sup')
        supplier_description = request.form.get('supplier_description')
        extra_info = request.form.get('extra_info')
        rating = 0  # Default rating for new suppliers

        # Validation checks
        if not commission.isdigit():
            flash('Commission must be a whole number (integer).', category='error')
            return redirect(url_for('views_creator.supplier'))

        if len(phone_number) > 11 or len(phone_number2) > 11:
            flash('Phone numbers must not exceed 11 characters.', category='error')
            return redirect(url_for('views_creator.supplier'))

        # Proceed if validation passes
        new_supplier = Supplier_info8(
            fullname=fullname,
            supplier_type=supplier_type,
            commission=commission,
            phone_number=phone_number,
            phone_number2=phone_number2,
            email_sup=email_sup,
            supplier_description=supplier_description,
            extra_info=extra_info,
            user_id=current_user.id,
            rating=rating  # Associate the supplier with the current user
        )
        db.session.add(new_supplier)
        db.session.commit()

        data_to_append = [fullname, "0", commission]

        # Open the CSV file in append mode
        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            # Append the new row
            writer.writerow(data_to_append)

        # Append to specific supplier type CSVs based on the supplier_type
            if supplier_type == "Cake":
                supplier_csv = cake
            elif supplier_type == "Digital_Printing":
                supplier_csv = digital_printing
            elif supplier_type == "Event_Planner":
                supplier_csv = event_planner
            elif supplier_type == "Grazing_Table":
                supplier_csv = grazing_table
            elif supplier_type == "Makeup_and_Hair":
                supplier_csv = makeup_and_Hair
            elif supplier_type == "Photobooth":
                supplier_csv = photobooth
            elif supplier_type == "Photographer":
                supplier_csv = photographer
            elif supplier_type == "Catering":
                supplier_csv = catering
            elif supplier_type == "Church":
                supplier_csv = church
            elif supplier_type == "Event_Stylist":
                supplier_csv = event_stylist
            elif supplier_type == "Events_Place":
                supplier_csv = events_place
            elif supplier_type == "Lights_and_Sounds":
                supplier_csv = lights_and_sounds
            else:
                supplier_csv = None

            # Append data to the specific supplier type CSV file if a match is found
            if supplier_csv:
                with open(supplier_csv, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(data_to_append)
            
            def read_csv(file_path, arr):
                with open(file_path, mode='r', newline='') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    for row in csv_reader:
                        thing = Thing(name=row['name'], rating=int(row['rating']), price=float(row['price']))
                        arr.append(thing)
            
            read_csv(csv_file_path, things_list)
            read_csv(cake , cake_arr)
            read_csv(digital_printing , digital_printing_arr)
            read_csv(event_planner , event_planner_arr)
            read_csv(grazing_table , grazing_table_arr)
            read_csv(makeup_and_Hair , makeup_and_hair_arr)
            read_csv(photobooth , photobooth_arr)
            read_csv(photographer , photographer_arr)

            read_csv(catering, catering_arr)
            read_csv(church, church_arr)
            read_csv(event_stylist, event_stylist_arr)
            read_csv(events_place, events_place_arr)
            read_csv(lights_and_sounds, lights_and_sounds_arr)


        # Append to specific supplier type arrays based on the supplier_type

        return redirect(url_for('views_creator.supplier'))  # Redirect to avoid resubmission on refresh

    return render_template('supplier.html', user=current_user)

###########################################################################################################################################################################

@views_creator.route('/supplier_rating_feedback', methods=['GET'])
@login_required
def supplier_rating_feedback():
    # Fetch the logged-in supplier's info (assuming the current user is a supplier)
    supplier_info = Supplier_info8.query.filter_by(user_id=current_user.id).all()

    if not supplier_info:
        flash('You have no reviews or feedback yet.', category='info')
        return redirect(request.url)

    return render_template('supplier_rating_feedback.html', user=current_user, supplier_info=supplier_info)

###########################################################################################################################################################################

@views_creator.route('/supplier_requests', methods=['GET'])
@login_required
def supplier_requests():
    # Fetch supplier requests linked to the current user as the event creator
    supplier_requests = Supplier_Req_Jobs3.query.all()

    # Fetch accepted jobs from the SupplierJobs3 table
    accepted_jobs = SupplierJobs3.query.all()

    # Retrieve supplier information for the current user
    supplier_info = Supplier_info8.query.filter_by(user_id=current_user.id).first()

    fullname = current_user.role + " : " +  current_user.first_name + " " + current_user.last_name

    return render_template('supplier_requests.html', user=current_user, fullname=fullname, supplier_info=supplier_info, supplier_requests=supplier_requests, accepted_jobs=accepted_jobs)

###########################################################################################################################################################################

@views_creator.route('/accept_request', methods=['POST'])
@login_required
def accept_request():
    request_id = request.form.get('request_id')

    if not request_id:
        flash("Request ID not found!", category='error')
        return redirect(url_for('views_creator.supplier_requests'))

    hire_request = Supplier_Req_Jobs3.query.get(request_id)
    supplier_info = Supplier_info8.query.filter_by(user_id=current_user.id).first()

    if hire_request and supplier_info:
        if hire_request.req_event_type == "Client-Help":
            # Saving to Client_Hired_Suppliers3 and using client_id from hire_request
            hired_supplier = Client_Hired_Suppliers3(
                event_id=hire_request.id,
                user_id=hire_request.client_id,  # Save the client ID from the request
                supplier_fullname=supplier_info.fullname,
                supplier_type=supplier_info.supplier_type,
                commission=supplier_info.commission,
                phone_number=supplier_info.phone_number,
                phone_number2=supplier_info.phone_number2,
                email_sup=supplier_info.email_sup,
                supplier_description=supplier_info.supplier_description,
                extra_info=supplier_info.extra_info,
                over_all_rating=supplier_info.over_all_rating
            )

            try:
                db.session.add(hired_supplier)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Error saving supplier to Client_Hired_Suppliers3: {e}", category='error')
                return redirect(url_for('views_creator.supplier_requests'))
        else:
            # Handle saving to HiredSuppliers3 if the event type is not "Client-Help"
            hired_supplier = HiredSuppliers3(
                event_id=hire_request.id,  # Assuming this links to the event being hired for
                user_id=hire_request.supplier_id,  # Link to the user who made the request
                supplier_fullname=supplier_info.fullname,
                supplier_type=supplier_info.supplier_type,
                commission=supplier_info.commission,
                phone_number=supplier_info.phone_number,
                phone_number2=supplier_info.phone_number2,
                email_sup=supplier_info.email_sup,
                supplier_description=supplier_info.supplier_description,
                extra_info=supplier_info.extra_info,
                over_all_rating=supplier_info.over_all_rating
            )

            try:
                db.session.add(hired_supplier)
                db.session.commit()
                print("Supplier info saved to HiredSuppliers3.")
            except Exception as e:
                db.session.rollback()
                print(f"Error saving supplier to HiredSuppliers3: {e}")
                flash(f"Error saving supplier to HiredSuppliers3: {e}", category='error')
                return redirect(url_for('views_creator.supplier_requests'))

        # Add the new job to the SupplierJobs3 table as before
        new_job = SupplierJobs3(
            supplier_id=hire_request.supplier_id,
            job_event_creator=hire_request.req_event_creator,
            job_event_name=hire_request.req_event_name,
            job_event_type=hire_request.req_event_type,
            job_room_code=hire_request.req_room_code,
            job_start_date=hire_request.req_start_date,
            job_end_date=hire_request.req_end_date
        )

        # Add the new job to the database
        try:
            db.session.add(new_job)
            db.session.commit()
            print("Job data successfully transferred.")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving job data: {e}")
            flash(f"Error saving job data: {e}", category='error')
            return redirect(url_for('views_creator.supplier_requests'))

        # Delete the original request
        try:
            db.session.delete(hire_request)
            db.session.commit()  # Commit the deletion
            flash('Request accepted and job created, supplier info saved!', category='success')
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting request: {e}")
            flash(f"Error deleting request: {e}", category='error')
    else:
        flash(f"Request with ID {request_id} not found!", category='error')

    return redirect(url_for('views_creator.supplier_requests'))

@views_creator.route('/client_suppliers_hired')
@login_required
def client_suppliers_hired():
    # Query all hired suppliers related to the current user
    hired_suppliers = Client_Hired_Suppliers3.query.filter_by(user_id=current_user.id).all()

    return render_template('client_suppliers_hired.html', user=current_user, hired_suppliers=hired_suppliers)
########################################################################################################################################################################### Client
########################################################################################################################################################################### Client

@views_creator.route('/create_event_profile_client')
@login_required
def create_event_profile_client():
    # Get the current user
    user = current_user

    # Pass the user data and images to the template
    return render_template('create_event_profile.html', user=user)
########################################################################################################################################################################### 

@views_creator.route('/client', methods=['GET', 'POST'])
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
        new_event = Client_events6(
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

###########################################################################################################################################################################

@views_creator.route('/client_events', methods=['POST', 'GET'])
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

###########################################################################################################################################################################

@views_creator.route('/delete_supplier', methods=['POST'])
@login_required
def delete_supplier():
    data = request.get_json()  # Get the JSON data from the request
    event_id = data.get('event_id')
    supplier_name = data.get('supplier_name')

    # Fetch the event by ID
    event = Client_events6.query.filter_by(id=event_id, user_id=current_user.id).first()

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

###########################################################################################################################################################################

@views_creator.route('/client_delete_event', methods=['POST'])
@login_required
def client_delete_event():
    data = request.get_json()
    event_id = data.get('event_id')

    # Fetch the event by ID
    event = Client_events6.query.filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        return jsonify({'success': False, 'message': 'Event not found'}), 404

    # Delete the event from the database
    db.session.delete(event)
    db.session.commit()

    return jsonify({'success': True})

###########################################################################################################################################################################

@views_creator.route('/client_hire_supplier', methods=['POST', 'GET'])
def client_hire_supplier():
    if request.method == 'POST':
        # Get the supplier name from the form (sent via JavaScript)
        supplier_name = request.form.get('supplier_name')
        
        # Query the database for the supplier details using the "fullname" field in Supplier_info8 table
        supplier = Supplier_info8.query.filter_by(fullname=supplier_name).first()

        if supplier:
            # Redirect to the client_send_request page with the supplier details
            return render_template(
                "client_send_request.html", user=current_user, 
                supplier_name=supplier.fullname,
                supplier_email=supplier.email_sup,
                supplier_phone=supplier.phone_number,
                supplier_phone2=supplier.phone_number2,
                over_all_rating=supplier.over_all_rating,
                commission=supplier.commission,
                supplier_type=supplier.supplier_type,
                supplier_description=supplier.supplier_description,
                extra_info=supplier.extra_info

            )
        else:
            flash('Supplier not found', category='error')
            return redirect(url_for('client_hire_supplier'))

    # Rendering the supplier list for GET request
    return render_template(
        "client_hire_supplier.html", 
        user=current_user, 
        name=current_user.first_name, 
        things_list=things_list, 
        cake1=cake1, 
        digital_printing1=digital_printing1, 
        event_planner1=event_planner1, 
        grazing_table1=grazing_table1, 
        makeup_and_hair1=makeup_and_hair1, 
        photobooth1=photobooth1, 
        photographer1=photographer1, 
        catering1=catering1, 
        church1=church1, 
        event_stylist1=event_stylist1, 
        events_place1=events_place1, 
        lights_and_sounds1=lights_and_sounds1
    )

###########################################################################################################################################################################

@views_creator.route('/client_send_request', methods=['POST', 'GET'])
@login_required
def client_send_request():
    if request.method == 'POST':
        job_event_name = request.form.get('job_event_name')
        job_event_type = request.form.get('job_event_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
        
        supplier_name = request.form.get('supplier_name')
        client_id = current_user.id  # Use the current user's ID as the client ID

        supplier = Supplier_info8.query.filter_by(fullname=supplier_name).first()

        if supplier:
            room_code = generate_unique_code()
            session["room"] = room_code
            session["name"] = f"{current_user.first_name} {current_user.last_name}"

            new_request = Supplier_Req_Jobs3(
                supplier_id=supplier.id,
                req_event_creator=f"{current_user.first_name} {current_user.last_name}",
                req_event_name=job_event_name,
                req_event_type=job_event_type,
                req_room_code=room_code,
                req_start_date=start_date,
                req_end_date=end_date,
                client_id=client_id  # Add client ID to the request
            )

            try:
                db.session.add(new_request)
                db.session.commit()
                flash('Request sent successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"Error saving request: {e}", 'error')

            return redirect(url_for('views_creator.client_hire_supplier'))
        else:
            flash('Supplier not found', 'error')
            return redirect(url_for('views_creator.client_hire_supplier'))
    
    return render_template("client_send_request.html")



