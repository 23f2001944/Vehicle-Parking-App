import matplotlib.pyplot as plt
from models import ParkingLot

parking_lots = ParkingLot.query.all()

# Initialize lists
lot_names = []
revenues = []
total_spots = []
available_spots = []

for lot in parking_lots:
    lot_names.append(f"Lot {lot.id}")
    
    # Revenue calculation: sum of costs of all reservations in this lot
    lot_revenue = sum(
        res.parking_cost or 0
        for spot in lot.spots
        for res in spot.reservations
    )
    revenues.append(lot_revenue)

    # Spot counts
    total_spots.append(len(lot.spots))
    available = sum(1 for spot in lot.spots if spot.status)
    available_spots.append(available)

# Plot revenue bar chart
plt.figure(figsize=(8, 5))
plt.bar(lot_names, revenues, color='skyblue')
plt.title('Revenue from Each Parking Lot')
plt.xlabel('Parking Lot')
plt.ylabel('Revenue (₹)')
plt.tight_layout()
plt.savefig('/static/images/revenue_chart.png')
plt.close()

# Plot total vs available spots stacked bar chart
x = range(len(lot_names))
plt.figure(figsize=(8, 5))
plt.bar(x, total_spots, label='Total Spots', color='lightgray')
plt.bar(x, available_spots, label='Available Spots', color='green')
plt.xticks(x, lot_names)
plt.title('Total vs Available Spots')
plt.xlabel('Parking Lot')
plt.ylabel('Number of Spots')
plt.legend()
plt.tight_layout()
plt.savefig('/static/images/spots_chart.png')
plt.close()