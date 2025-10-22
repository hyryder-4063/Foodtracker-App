import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const MyApp());
}

const backendUrl = 'https://flat-weeks-build.loca.lt'; //Ngrok

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Food Tracker',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  String? userName;

  @override
  void initState() {
    super.initState();
    loadUser();
  }

  Future<void> loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    final name = prefs.getString('user_name');
    setState(() {
      userName = name;
    });
    if (name != null) {
      navigateHome();
    }
  }

  void navigateHome() {
    Navigator.pushReplacement(
        context,
        MaterialPageRoute(
            builder: (_) => MyHomePage(
                  userName: userName!,
                )));
  }

  @override
  Widget build(BuildContext context) {
    return userName == null
        ? const UserSetupScreen()
        : const Center(child: CircularProgressIndicator());
  }
}

class UserSetupScreen extends StatefulWidget {
  const UserSetupScreen({super.key});

  @override
  State<UserSetupScreen> createState() => _UserSetupScreenState();
}

class _UserSetupScreenState extends State<UserSetupScreen> {
  final _controller = TextEditingController();

  void saveUser() async {
    final name = _controller.text.trim();
    if (name.isEmpty) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_name', name);
    Navigator.pushReplacement(
        context,
        MaterialPageRoute(
            builder: (_) => MyHomePage(
                  userName: name,
                )));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Enter Your Name',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _controller,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'Your name',
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton(onPressed: saveUser, child: const Text('Continue'))
            ],
          ),
        ),
      ),
    );
  }
}

class MyHomePage extends StatefulWidget {
  final String userName;
  const MyHomePage({super.key, required this.userName});

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  String? selectedMealType;
  DateTime selectedDate = DateTime.now();
  List<dynamic> foods = [];
  Map<String, dynamic> mealEntry = {
    'food_item_id': null,
    'quantity_g': 0,
    'notes': '',
  };
  List<dynamic> monthlySummary = [];
  Map<String, dynamic>? dailySummary;

  final mealTypes = ['Breakfast', 'Lunch', 'Snack', 'Dinner'];

  @override
  void initState() {
    super.initState();
    fetchFoods();
    fetchMonthlySummary();
    fetchDailySummary();
  }

  Future<void> fetchFoods() async {
    try {
      final response = await http.get(Uri.parse('$backendUrl/foods/'));
      if (response.statusCode == 200) {
        setState(() {
          foods = json.decode(response.body);
        });
      }
    } catch (e) {
      print('Error fetching foods: $e');
    }
  }

  Future<void> fetchMonthlySummary() async {
    try {
      final year = selectedDate.year;
      final month = selectedDate.month;
      final response =
          await http.get(Uri.parse('$backendUrl/monthly-summary/1/$year/$month'));
      if (response.statusCode == 200) {
        setState(() {
          monthlySummary = json.decode(response.body);
        });
      }
    } catch (e) {
      print('Error fetching monthly summary: $e');
    }
  }

  Future<void> fetchDailySummary() async {
    try {
      final dateStr = DateFormat('yyyy-MM-dd').format(selectedDate);
      final response =
          await http.get(Uri.parse('$backendUrl/daily-summary/1/$dateStr'));
      if (response.statusCode == 200) {
        setState(() {
          dailySummary = json.decode(response.body);
        });
      }
    } catch (e) {
      print('Error fetching daily summary: $e');
    }
  }

  void submitMeal() async {
    if (mealEntry['food_item_id'] == null) return;

    final mealData = {
      "user_id": 1,
      "date": DateFormat('yyyy-MM-dd').format(selectedDate),
      "meal_type": selectedMealType!.toLowerCase(),
      "entries": [mealEntry]
    };

    try {
      final response = await http.post(
        Uri.parse('$backendUrl/meals/'),
        headers: {"Content-Type": "application/json"},
        body: json.encode(mealData),
      );
      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text("Amazing job ${widget.userName}!",
                style: const TextStyle(fontWeight: FontWeight.bold))));
        setState(() {
          mealEntry = {'food_item_id': null, 'quantity_g': 0, 'notes': ''};
        });
        fetchMonthlySummary();
        fetchDailySummary();
      }
    } catch (e) {
      print('Error submitting meal: $e');
    }
  }

  Future<void> pickDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: selectedDate,
      firstDate: DateTime(2023),
      lastDate: DateTime.now(),
    );
    if (date != null) {
      setState(() {
        selectedDate = date;
      });
      fetchMonthlySummary();
      fetchDailySummary();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text('Welcome, ${widget.userName}!'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  'Selected Date: ${DateFormat('dd MMM yyyy').format(selectedDate)}',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  onPressed: pickDate,
                  icon: const Icon(Icons.calendar_today),
                )
              ],
            ),
            const SizedBox(height: 10),
            const Text(
              "Select Meal",
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: mealTypes.map((type) {
                final isSelected = selectedMealType == type;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor:
                            isSelected ? Colors.deepPurple : Colors.grey[300],
                        foregroundColor:
                            isSelected ? Colors.white : Colors.black,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        textStyle: const TextStyle(fontSize: 14),
                      ),
                      onPressed: () {
                        setState(() {
                          selectedMealType = type;
                        });
                      },
                      child: Text(type, overflow: TextOverflow.ellipsis),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),
            if (selectedMealType != null)
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Enter Food for $selectedMealType',
                        style: const TextStyle(
                            fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 10),

                      // Food selection dropdown
                      DropdownButton<int>(
                        isExpanded: true,
                        value: mealEntry['food_item_id'],
                        hint: const Text('Select Food'),
                        items: foods
                            .map((f) => DropdownMenuItem<int>(
                                  value: f['id'],
                                  child: Text(f['name']),
                                ))
                            .toList(),
                        onChanged: (val) {
                          setState(() {
                            mealEntry['food_item_id'] = val;
                          });
                        },
                      ),
                      const SizedBox(height: 10),

                      // Quantity input
                      TextFormField(
                        decoration: const InputDecoration(
                            labelText: 'Quantity (g)',
                            border: OutlineInputBorder()),
                        keyboardType: TextInputType.number,
                        onChanged: (val) {
                          setState(() {
                            mealEntry['quantity_g'] =
                                double.tryParse(val) ?? 0;
                          });
                        },
                      ),
                      const SizedBox(height: 10),

                      // Notes input (optional)
                      TextFormField(
                        decoration: const InputDecoration(
                            labelText: 'Notes (optional)',
                            border: OutlineInputBorder()),
                        onChanged: (val) {
                          setState(() {
                            mealEntry['notes'] = val;
                          });
                        },
                      ),
                      const SizedBox(height: 10),

                      // Submit button
                      Center(
                        child: ElevatedButton(
                          onPressed: submitMeal,
                          child: const Text('Submit Meal'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 20),

            // Daily summary card
            if (dailySummary != null)
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Daily Summary',
                        style: TextStyle(
                            fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 10),
                      Text(
                          'Calories: ${dailySummary!['totals']['kcal']} kcal'),
                      Text(
                          'Carbs: ${dailySummary!['totals']['carbs_g']} g'),
                      Text(
                          'Protein: ${dailySummary!['totals']['protein_g']} g'),
                      Text('Fat: ${dailySummary!['totals']['fat_g']} g'),
                      Text(
                          'Fiber: ${dailySummary!['totals']['fiber_g']} g'),
                      const SizedBox(height: 10),
                      Text(
                        dailySummary!['nudges'][0],
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, color: Colors.blue),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 20),

            // Monthly summary chart
            if (monthlySummary.isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Monthly Summary',
                    style:
                        TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    height: 300,
                    child: MonthlyChart(data: monthlySummary),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

// Monthly Chart Widget
class MonthlyChart extends StatelessWidget {
  final List<dynamic> data;

  const MonthlyChart({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    return LineChart(
      LineChartData(
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            axisNameWidget: const Text('Calories (kcal)',
                style: TextStyle(fontWeight: FontWeight.bold)),
            sideTitles: SideTitles(showTitles: true, reservedSize: 40),
          ),
          bottomTitles: AxisTitles(
            axisNameWidget: const Text('Date',
                style: TextStyle(fontWeight: FontWeight.bold)),
            sideTitles: SideTitles(
              showTitles: true,
              interval: 1,
              getTitlesWidget: (value, meta) {
                int index = value.toInt();
                if (index >= 0 && index < data.length) {
                  final dateStr = DateFormat('d MMM')
                      .format(DateTime.parse(data[index]['date']));
                  return Text(dateStr, style: const TextStyle(fontSize: 10));
                }
                return const SizedBox();
              },
            ),
          ),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: data
                .asMap()
                .entries
                .map((e) => FlSpot(
                    e.key.toDouble(), e.value['totals']['kcal'] + 0.0))
                .toList(),
            isCurved: true,
            color: Colors.red,
            barWidth: 3,
            belowBarData:
                BarAreaData(show: true, color: Colors.red.withOpacity(0.15)),
          ),
          LineChartBarData(
            spots: data
                .asMap()
                .entries
                .map((e) => FlSpot(
                    e.key.toDouble(), e.value['totals']['protein_g'] + 0.0))
                .toList(),
            isCurved: true,
            color: Colors.green.shade700.withOpacity(0.8), // pastel dark green
            barWidth: 3,
            belowBarData: BarAreaData(
                show: true, color: Colors.green.shade700.withOpacity(0.15)),
          ),
        ],
        gridData: FlGridData(show: true),
        borderData: FlBorderData(show: true),
      ),
    );
  }
}
