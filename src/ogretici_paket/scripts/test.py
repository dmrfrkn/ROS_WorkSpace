from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import rospy



rospy.init_node("test_node",anonymous=True)

# Uçağa bağlan
vehicle = connect('127.0.0.1:14550', wait_ready=True)

# Uçuş modunu değiştir
def set_mode(mode):
    while vehicle.mode != VehicleMode(mode):
        vehicle.mode = VehicleMode(mode)
        print(f'Mode: {mode}')
        time.sleep(1)

# Hedef konumuna uçuş
def fly_to_target(target_location):
    print("Arming motors")
    vehicle.armed = True
    
    while not vehicle.armed:
        print("Waiting for arming...")
        time.sleep(1)
    
    print("Taking off")
    vehicle.simple_takeoff(10)  # 10 metre yüksekliğe kalkış
    
    # Kalkışın tamamlanmasını bekle
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= 9.5:
            print("Reached target altitude")
            break
        time.sleep(1)
    
    print(f"Flying to target: {target_location}")
    vehicle.simple_goto(target_location)

    # Hedef konumuna ulaşıp ulaşmadığını kontrol et
    while True:
        current_location = vehicle.location.global_frame
        distance = get_distance_metres(current_location, target_location)
        print(f"Distance to target: {distance}")
        
        if distance < 1:
            print("Reached target location")
            break
        time.sleep(1)

# Hedef koordinatlar
target_location = LocationGlobalRelative(37.7749, -122.4194, 10)  # Örnek koordinatlar (Enlem, Boylam, Yükseklik)

# Modları ayarla ve hedefe uç
set_mode("GUIDED")
fly_to_target(target_location)

# Uçuşu sonlandır
print("Landing")
set_mode("LAND")

# Bağlantıyı kapat
vehicle.close()

print("Mission completed")
