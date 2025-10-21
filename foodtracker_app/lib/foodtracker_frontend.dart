import 'package:flutter/material.dart';

void main() {
  runApp(FoodTrackerApp());
}

class FoodTrackerApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Food Tracker',
      theme: ThemeData(
        primarySwatch: Colors.green,
      ),
      home: MealEntryScreen(),
    );
  }
}

class MealEntryScreen extends StatefulWidget {
  @override
  _MealEntryScreenState createState() => _MealEntryScreenState();
}

class _MealEntryScreenState extends State<MealEntryScreen> {
  DateTime selectedDate = DateTime.now();
  String mealType = 'Breakfast';
  final TextEditingController mealNameController = TextEditingController();
  final TextEditingController quantityController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Enter Your Meal'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Date picker
            Text('Date: ${selectedDate.toLocal()}'.split(' ')[0]),
            ElevatedButton(
              onPressed: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: selectedDate,
                  firstDate: DateTime(2020),
                  lastDate: DateTime(2100),
                );
                if (picked != null && picked != selectedDate) {
                  setState(() {
                    selectedDate = picked;
                  });
                }
              },
              child: Text('Select Date'),
            ),
            SizedBox(height: 16),

            // Meal type dropdown
            DropdownButton<String>(
              value: mealType,
              items: ['Breakfast', 'Lunch', 'Dinner']
                  .map((e) => DropdownMenuItem(
                        child: Text(e),
                        value: e,
                      ))
                  .toList(),
              onChanged: (val) {
                setState(() {
                  mealType = val!;
                });
              },
            ),
            SizedBox(height: 16),

            // Meal name
            TextField(
              controller: mealNameController,
              decoration: InputDecoration(labelText: 'Meal Name'),
            ),
            SizedBox(height: 16),

            // Quantity
            TextField(
              controller: quantityController,
              decoration: InputDecoration(labelText: 'Quantity'),
              keyboardType: TextInputType.number,
            ),
            SizedBox(height: 24),

            // Save button
            Center(
              child: ElevatedButton(
                onPressed: () {
                  // TODO: Send to backend
                  print('Date: $selectedDate, Meal: $mealType, Name: ${mealNameController.text}, Quantity: ${quantityController.text}');
                },
                child: Text('Save Meal'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
