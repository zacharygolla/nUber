from app import app, db
from flask_restful import Resource, Api, reqparse
from app.models import AdminModel, RiderModel, DriverModel
from flask import jsonify, abort
from sqlalchemy.exc import DatabaseError
from app.serializers import admin_schema_many, rider_schema_many, driver_schema_many, rider_schema
from app.haversine import Haversine
from googlemaps import distance_matrix
from googlemaps import client

api = Api(app)


class UpdateDriverAvailability(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('available', type=bool)

        self.args = parser.parse_args()

        super().__init__()

    def put(self):

        # Query the driver from database
        driver = DriverModel.query.filter_by(id=self.args['id']).first()

        if driver is None:
            abort(502, 'Driver was not found')

        else:
            try:

                driver.available = self.args['available']

                db.session.commit()
            except:
                abort(502, 'Driver availability was not updated')

        return jsonify(message='Driver availability was updated')


class SelectDriver(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('driver_id', type=int)
        parser.add_argument('rider_id', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def put(self):

        # Query both the driver and the rider
        driver = DriverModel.query.filter_by(id=self.args['driver_id']).first()
        rider = RiderModel.query.filter_by(id=self.args['rider_id']).first()

        if rider.name != rider.groupHost and rider.groupHost != None:
            abort(502, 'Rider was not group host.')
            
        # Check if the driver is not in the database
        if driver is None:
            abort(502, 'Driver was not found')

        # Check to see if the rider is not in the database
        elif rider is None:
            abort(502, 'Rider was not found')

        # Check driver availability
        elif not driver.available:
            abort(502, 'Driver is not available')

        else:
            try:
                rider.selected_driver = self.args['driver_id']
                driver.selected_rider = self.args['rider_id']
                driver.available = False
                db.session.commit()

            except:
                abort(502, 'Driver was not assigned to rider')

        return jsonify(message='Driver was successfully added to rider')


'''
    Given a rider, if that rider has a selected driver, return that driver's current location
'''


class GetRiderDriverLocation(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('rider_id', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        # Query the rider
        rider = RiderModel.query.filter_by(id=self.args['rider_id']).first()

        # Check to see if the rider is not in the database
        if rider is None:
            abort(502, 'Rider does not exist')

        # If rider exists query for its selected driver
        driver = DriverModel.query.filter_by(id=rider.selected_driver).first()

        # Check to see if rider currently has a driver
        if driver is None:
            abort(502, 'Driver does not exist')

        # Check to see if driver has a set location
        elif driver.long is None or driver.lat is None:
            abort(502, 'Driver location is not properly set')

        # Print the rider's driver's long and lat
        else:
            try:
                return jsonify(driver_long=driver.long, driver_lat=driver.lat)
            except:
                abort(502, 'Driver location could not be determined')


'''
    Given driver and rider id, get latitude and longitude as location for the rider.
'''


class GetRiderLocation(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('driver_id', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        driver = DriverModel.query.filter_by(id=self.args['driver_id']).first()
        rider = RiderModel.query.filter_by(id=driver.selected_rider).first()

        if driver is None:
            abort(502, 'Driver was not found')

        if driver.selected_rider is None:
            abort(502, 'Driver does not have a rider')

        if rider is None:
            abort(502, 'Rider was not found')

        if rider.lat is None or rider.long is None:
            abort(502, 'Rider does not have a set location')

        return jsonify(selected_rider_lat=rider.lat, selected_rider_long=rider.long)


class GetRiderCharge(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('driver_id', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        # add if to check whether rider is groupHost or not
        driver = DriverModel.query.filter_by(id=self.args['driver_id']).first()
        rider = RiderModel.query.filter_by(id=driver.selected_rider).first()
        group = RiderModel.query.filter_by(groupHost=rider.groupHost).all()
        numRiders = len(group)
        
        # check to see if driver exists
        if driver is None:
            abort(502, 'Driver was not found in the database')

        # check to see if driver has a current rider
        elif driver.selected_rider is None:
            abort(502, 'Driver does not have a currently selected rider')

        # check to see if rider has a currently selected destination (maybe check this when rider added to driver)
        elif rider.destination is None:
            abort(502, 'Rider does not have a currently selected destination')

        # check to see if rider has a currently set location
        elif rider.long is None or rider.lat is None:
            abort(502, 'Riders location is not properly set')

        # find the distance between the riders location and his destionation and set a price accordingly
        else:
            try:
                # Need to add the functionality with Google's API

                #Origins will be passed as longitude/latitude and destinations will be passed as a physical address
                origins = rider.lat, rider.long
                destination = rider.destination

                #call the client function and provide API
                gmaps = client.Client(key="AIzaSyDJpvTBLUVor9hgDQyT3rp6jxzWUzFdD2Q")

                #Distance is calculated in meters, converted to miles, and multiplied by 1.50 (cost of driving a mile)
                distance = distance_matrix.distance_matrix(gmaps, origins, destination, mode='driving')["rows"][0]["elements"][0]["distance"]["value"]
                distance = distance*0.000621371
                cost = distance*1.50
                indCost = cost/numRiders #cost for individual rider in group

                for groupMember in group:
                    groupMember.outstandingBalance = indCost
                    print(groupMember.name)

                db.session.commit()
                
                return jsonify(num_rider=numRiders, cost=cost, cost_per_rider=indCost)

            except:
                abort(502, 'Rider''s charge could not be determined')

'''
    Given a driver id, get the destination of the associated rider
'''


class GetRiderDest(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('driver_id', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        driver = DriverModel.query.filter_by(id=self.args['driver_id']).first()
        rider = RiderModel.query.filter_by(id=driver.selected_rider).first()

        if driver is None:
            abort(502, 'Driver was not found')

        elif driver.selected_rider is None:
            abort(502, 'Driver does not have a rider')

        elif rider is None:
            abort(502, 'Rider was not found')

        elif rider.destination is None:
            abort(502, 'Rider does not have a destination')

        return jsonify(rider_destination=rider.destination)


'''
    Given a rider id and destination, set the target destination of the corresponding rider
'''


class SetRiderDest(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('destination', type=str)

        self.args = parser.parse_args()

        super().__init__()

    def put(self):
        rider = RiderModel.query.filter_by(id=self.args['id']).first()

        if rider is None:
            abort(502, 'Rider was not found')

        else:
            try:
                rider.destination = self.args['destination']
                db.session.commit()

            except:
                abort(503, 'Rider destination was not updated')

        return jsonify(message='Rider destination successfully updated')


'''
    Given a driver id and a new set of coordinates, update the driver with the set of new coordinates
'''


class UpdateDriverPosition(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('lat', type=float)
        parser.add_argument('long', type=float)

        self.args = parser.parse_args()

        super().__init__()

    def put(self):
        driver = DriverModel.query.filter_by(id=self.args['id']).first()

        if driver is None:
            abort(502, 'Driver was not found')

        else:
            try:
                driver.lat = self.args['lat']
                driver.long = self.args['long']
                db.session.commit()

            except:
                abort(502, 'Driver coordinates were not updated')

        return jsonify(message='Driver coordinates successfully updated')


'''
    Given a rider id and a radius, display all the available drivers within the specified radius. 
    To calculate distance, we will use the haversine formula, which takes in two sets of longitude
    and latitude and displays the distance in miles.  
'''


class GetDrivers(Resource):

    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('radius', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        rider = RiderModel.query.filter_by(id=self.args['id']).first()

        if rider is None:
            return abort(502, 'The rider was not in the database')

        else:

            drivers = DriverModel.query.all()

            for driver in drivers:
                if Haversine.calculate_distance(rider.lat, rider.long, driver.lat, driver.long) > self.args['radius'] \
                        or not driver.available:
                    drivers.remove(driver)

            return jsonify(available_drivers=driver_schema_many.dump(drivers).data)


'''
Driver class allows drivers to be added, removed, and modified in the database.
'''


class Driver(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('name', type=str)
        parser.add_argument('available', type=bool)
        parser.add_argument('lat', type=float)
        parser.add_argument('long', type=float)
        parser.add_argument('amountMoney', type=float)
        parser.add_argument('selected_rider', type=int)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        drivers = DriverModel.query.all()
        return jsonify(drivers=driver_schema_many.dump(drivers).data)

    def post(self):
        try:
            new_driver = DriverModel(**self.args)
            db.session.add(new_driver)
            db.session.commit()

        except DatabaseError:
            return abort(500, 'Driver was not added to the database!')

        return jsonify(message='Driver successfully created!')

    def put(self):

        driver = DriverModel.query.filter_by(id=self.args['id']).first()

        if driver:
            try:
                driver.id = self.args['id']
                driver.name = self.args['name']
                driver.lat = self.args['lat']
                driver.long = self.args['long']
                driver.selected_rider = self.args['selected_rider']
                driver.available = self.args['available']
                driver.amountMoney = self.args['amountMoney']
                db.session.commit()
            except DatabaseError:
                return abort(501, 'The driver was not updated!')

            return jsonify(message="Driver was successfully updated!")

        else:
            return abort(500, 'The driver did not exist')

    def delete(self):
        driver = DriverModel.query.filter_by(id=self.args['id']).first()

        if driver:
            try:
                db.session.delete(driver)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The item was not deleted')

            return jsonify(message="The driver was successfully deleted")

        else:
            return abort(503, 'The driver did not exist')


'''
    Given a rider id and a new set of coordinates, update the rider with the set of new coordinates
'''


class UpdateRiderPosition(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('lat', type=float)
        parser.add_argument('long', type=float)

        self.args = parser.parse_args()

        super().__init__()

    def put(self):
        rider = RiderModel.query.filter_by(id=self.args['id']).first()

        if rider is None:
            abort(502, 'Rider was not found')

        else:
            try:
                rider.lat = self.args['lat']
                rider.long = self.args['long']
                db.session.commit()

            except:
                abort(502, 'Rider coordinates were not updated')

        return jsonify(message='Rider coordinates successfully updated')


'''
Rider class allows drivers to be added, removed, and modified in the database.
'''


class Rider(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('name', type=str)
        parser.add_argument('lat', type=float)
        parser.add_argument('long', type=float)
        parser.add_argument('groupHost', type=str)
        parser.add_argument('outstandingBalance', type=float)
        
        self.args = parser.parse_args()

        super().__init__()

    def post(self):
        try:
            new_rider = RiderModel(**self.args)
            db.session.add(new_rider)
            db.session.commit()

        except DatabaseError:
            return abort(500, 'Rider was not added to the database!')

        return jsonify(message='Rider successfully created!')

    def delete(self):
        rider = RiderModel.query.filter_by(id=self.args['id']).first()

        if rider:
            try:
                db.session.delete(rider)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The item was not deleted')

            return jsonify(message="The rider was successfully deleted")

        else:
            return abort(503, 'The rider did not exist')

    def put(self):

        rider = RiderModel.query.filter_by(id=self.args['id']).first()

        if rider:
            try:
                rider.id = self.args['id']
                rider.name = self.args['name']
                rider.lat = self.args['lat']
                rider.long = self.args['long']
                rider.groupHost = self.args['groupHost']
                rider.outstandingBalance = self.args['outstandingBalance']
                db.session.commit()
            except DatabaseError:
                return abort(501, 'The rider was not updated!')

            return jsonify(message="Rider was successfully updated!")

        else:
            return abort(500, 'The rider did not exist')

    def get(self):
        riders = RiderModel.query.all()
        print(riders)
        return jsonify(riders=rider_schema_many.dump(riders).data)


class Admin(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=int)
        parser.add_argument('name', type=str)

        self.args = parser.parse_args()

        super().__init__()

    def get(self):
        admins = AdminModel.query.all()
        print(admins)
        return jsonify(admins=admin_schema_many.dump(admins).data)

    def post(self):
        try:
            # AdminModel.create(**self.args)
            new_admin = AdminModel(**self.args)
            db.session.add(new_admin)
            db.session.commit()

        except DatabaseError:
            return abort(500, 'Admin was not added to the database!')

        return jsonify(message='Admin successfully created!')

    def put(self):

        admin = AdminModel.query.filter_by(id=self.args['id']).first()

        if admin:
            try:
                admin.id = self.args['id']
                admin.name = self.args['name']
                db.session.commit()
            except DatabaseError:
                return abort(501, 'The admin was not updated!')

            return jsonify(message="Admin was successfully updated!")

        else:
            return abort(500, 'The admin did not exist')

    def delete(self):
        admin = AdminModel.query.filter_by(id=self.args['id']).first()

        if admin:
            try:
                db.session.delete(admin)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The item was not deleted')

            return jsonify(message="The admin was successfully deleted")

        else:
            return abort(503, 'The admin did not exist')


# Admin Routes
api.add_resource(Admin, '/admin')
api.add_resource(Driver, '/admin/driver')
api.add_resource(Rider, '/admin/rider')

# Driver Routes
api.add_resource(UpdateDriverPosition, '/driver/update_position')
api.add_resource(UpdateDriverAvailability, '/driver/update_availability')
api.add_resource(GetRiderDest, '/driver/get_rider_destination')
api.add_resource(GetRiderLocation, '/driver/get_rider_location')
api.add_resource(GetRiderCharge, '/driver/get_rider_charge')

# Rider Routes
api.add_resource(SetRiderDest, '/rider/set_destination')
api.add_resource(UpdateRiderPosition, '/rider/update_position')
api.add_resource(SelectDriver, '/rider/select_driver')
api.add_resource(GetDrivers, '/rider/get_drivers')
api.add_resource(GetRiderDriverLocation, '/rider/get_driver_location')
