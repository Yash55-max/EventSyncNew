"""
Sustainability Tracking System for Event Management
Carbon Footprint Calculators, Eco-Friendly Suggestions, and Green Metrics
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

from app import db
from models import Event, User, EventAnalytics

logger = logging.getLogger(__name__)

class SustainabilityCategory(Enum):
    """Categories for sustainability tracking"""
    TRANSPORTATION = "transportation"
    VENUE = "venue"
    CATERING = "catering"
    MATERIALS = "materials"
    ENERGY = "energy"
    WASTE = "waste"
    ACCOMMODATION = "accommodation"
    DIGITAL = "digital"

class ImpactLevel(Enum):
    """Environmental impact levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class SustainabilityGoal(Enum):
    """Sustainability goals for events"""
    CARBON_NEUTRAL = "carbon_neutral"
    WASTE_FREE = "waste_free"
    LOCAL_SOURCING = "local_sourcing"
    RENEWABLE_ENERGY = "renewable_energy"
    SUSTAINABLE_TRANSPORT = "sustainable_transport"
    ECO_FRIENDLY_MATERIALS = "eco_friendly_materials"

@dataclass
class CarbonFootprint:
    """Carbon footprint calculation result"""
    total_co2_kg: float
    category_breakdown: Dict[str, float]
    per_attendee_kg: float
    comparison_data: Dict[str, Any]
    impact_level: ImpactLevel
    reduction_potential: float

@dataclass
class SustainabilityRecommendation:
    """Eco-friendly recommendation"""
    category: SustainabilityCategory
    title: str
    description: str
    impact_reduction: float  # kg CO2 saved
    cost_impact: str  # "neutral", "increase", "decrease"
    difficulty: str  # "easy", "moderate", "challenging"
    implementation_steps: List[str]
    estimated_savings: Dict[str, float]  # CO2, cost, etc.

@dataclass
class SustainabilityMetrics:
    """Overall sustainability metrics for an event"""
    carbon_footprint: CarbonFootprint
    sustainability_score: float  # 0-100
    goals_achieved: List[SustainabilityGoal]
    recommendations: List[SustainabilityRecommendation]
    green_badges: List[str]
    improvement_areas: List[str]

class CarbonFootprintCalculator:
    """Advanced carbon footprint calculator for events"""
    
    # Emission factors (kg CO2 equivalent per unit)
    EMISSION_FACTORS = {
        'transport': {
            'car_per_km': 0.12,  # per passenger km
            'bus_per_km': 0.03,  # per passenger km
            'train_per_km': 0.014,  # per passenger km
            'plane_domestic_per_km': 0.255,  # per passenger km
            'plane_international_per_km': 0.195,  # per passenger km
            'walking_cycling': 0.0
        },
        'venue': {
            'electricity_per_kwh': 0.4,  # kg CO2 per kWh
            'heating_gas_per_kwh': 0.2,  # kg CO2 per kWh
            'cooling_per_sqm_hour': 0.05,  # kg CO2 per sqm per hour
            'lighting_per_sqm_hour': 0.02  # kg CO2 per sqm per hour
        },
        'catering': {
            'meat_heavy_per_person': 5.2,  # kg CO2 per meal
            'meat_moderate_per_person': 3.8,  # kg CO2 per meal
            'vegetarian_per_person': 1.9,  # kg CO2 per meal
            'vegan_per_person': 1.1,  # kg CO2 per meal
            'local_food_reduction': 0.8,  # 20% reduction factor
            'organic_food_reduction': 0.9  # 10% reduction factor
        },
        'materials': {
            'paper_per_kg': 1.3,  # kg CO2 per kg
            'plastic_per_kg': 3.4,  # kg CO2 per kg
            'fabric_per_kg': 15.0,  # kg CO2 per kg
            'digital_alternative_reduction': 0.95  # 95% reduction
        },
        'waste': {
            'landfill_per_kg': 0.4,  # kg CO2 per kg waste
            'recycling_per_kg': 0.1,  # kg CO2 per kg waste
            'composting_per_kg': 0.05,  # kg CO2 per kg waste
            'food_waste_per_kg': 2.5  # kg CO2 per kg food waste
        },
        'accommodation': {
            'hotel_per_night_per_room': 30.0,  # kg CO2 per night
            'hostel_per_night_per_room': 15.0,  # kg CO2 per night
            'airbnb_per_night_per_room': 20.0,  # kg CO2 per night
            'green_certified_reduction': 0.7  # 30% reduction
        },
        'digital': {
            'streaming_per_hour_per_person': 0.0036,  # kg CO2 per hour
            'video_conference_per_hour_per_person': 0.00096,  # kg CO2 per hour
            'email_per_message': 0.000004,  # kg CO2 per email
            'cloud_storage_per_gb_per_month': 0.0065  # kg CO2 per GB
        }
    }
    
    def calculate_transportation_footprint(self, event_data: Dict) -> float:
        """Calculate transportation carbon footprint"""
        total_co2 = 0.0
        attendee_count = event_data.get('expected_attendees', 0)
        
        # Get transportation mode distribution
        transport_modes = event_data.get('transport_modes', {
            'car': 0.4,
            'public_transport': 0.3,
            'walking_cycling': 0.2,
            'plane': 0.1
        })
        
        # Average distances
        avg_distance_km = event_data.get('avg_attendee_distance', 25)
        international_attendees = event_data.get('international_attendees_ratio', 0.1)
        
        for mode, ratio in transport_modes.items():
            attendees_using_mode = attendee_count * ratio
            
            if mode == 'car':
                # Assume 2 people per car on average
                car_trips = attendees_using_mode / 2
                total_co2 += car_trips * avg_distance_km * 2 * self.EMISSION_FACTORS['transport']['car_per_km']
            
            elif mode == 'public_transport':
                # Mix of bus and train
                total_co2 += attendees_using_mode * avg_distance_km * 2 * (
                    0.7 * self.EMISSION_FACTORS['transport']['bus_per_km'] +
                    0.3 * self.EMISSION_FACTORS['transport']['train_per_km']
                )
            
            elif mode == 'plane':
                # Calculate flight emissions
                if international_attendees > 0:
                    intl_distance = event_data.get('avg_international_distance', 2000)
                    intl_attendees_count = attendee_count * international_attendees
                    total_co2 += intl_attendees_count * intl_distance * 2 * \
                                 self.EMISSION_FACTORS['transport']['plane_international_per_km']
                
                # Domestic flights
                domestic_flight_attendees = attendees_using_mode - (attendee_count * international_attendees)
                if domestic_flight_attendees > 0:
                    domestic_distance = event_data.get('avg_domestic_distance', 800)
                    total_co2 += domestic_flight_attendees * domestic_distance * 2 * \
                                 self.EMISSION_FACTORS['transport']['plane_domestic_per_km']
        
        return total_co2
    
    def calculate_venue_footprint(self, event_data: Dict) -> float:
        """Calculate venue carbon footprint"""
        total_co2 = 0.0
        
        # Venue specifications
        venue_size_sqm = event_data.get('venue_size_sqm', 500)
        event_duration_hours = event_data.get('duration_hours', 8)
        energy_source = event_data.get('energy_source', 'grid')  # grid, renewable, mixed
        
        # Electricity consumption
        electricity_kwh = venue_size_sqm * event_duration_hours * 0.1  # 0.1 kWh per sqm per hour
        if energy_source == 'renewable':
            electricity_co2 = electricity_kwh * 0.05  # Much lower emissions
        elif energy_source == 'mixed':
            electricity_co2 = electricity_kwh * 0.2  # 50% renewable
        else:
            electricity_co2 = electricity_kwh * self.EMISSION_FACTORS['venue']['electricity_per_kwh']
        
        total_co2 += electricity_co2
        
        # Heating/Cooling
        climate_control_kwh = venue_size_sqm * event_duration_hours * 0.05
        total_co2 += climate_control_kwh * self.EMISSION_FACTORS['venue']['heating_gas_per_kwh']
        
        # Additional venue factors
        if event_data.get('venue_certification') == 'green':
            total_co2 *= 0.7  # 30% reduction for green certified venues
        
        return total_co2
    
    def calculate_catering_footprint(self, event_data: Dict) -> float:
        """Calculate catering carbon footprint"""
        total_co2 = 0.0
        attendee_count = event_data.get('expected_attendees', 0)
        
        # Meal distribution
        meal_types = event_data.get('meal_distribution', {
            'meat_heavy': 0.3,
            'meat_moderate': 0.4,
            'vegetarian': 0.2,
            'vegan': 0.1
        })
        
        # Number of meals
        meals_per_person = event_data.get('meals_per_person', 2)
        
        for meal_type, ratio in meal_types.items():
            attendees_with_meal = attendee_count * ratio
            meal_emissions = attendees_with_meal * meals_per_person * \
                           self.EMISSION_FACTORS['catering'][f'{meal_type}_per_person']
            total_co2 += meal_emissions
        
        # Apply reductions for local/organic sourcing
        if event_data.get('local_sourcing_ratio', 0) > 0:
            local_reduction = event_data['local_sourcing_ratio'] * (1 - self.EMISSION_FACTORS['catering']['local_food_reduction'])
            total_co2 *= (1 - local_reduction)
        
        if event_data.get('organic_ratio', 0) > 0:
            organic_reduction = event_data['organic_ratio'] * (1 - self.EMISSION_FACTORS['catering']['organic_food_reduction'])
            total_co2 *= (1 - organic_reduction)
        
        return total_co2
    
    def calculate_materials_footprint(self, event_data: Dict) -> float:
        """Calculate materials carbon footprint"""
        total_co2 = 0.0
        attendee_count = event_data.get('expected_attendees', 0)
        
        # Material usage
        materials = event_data.get('materials', {
            'paper_kg': 0.1 * attendee_count,  # 100g per person
            'plastic_kg': 0.05 * attendee_count,  # 50g per person
            'fabric_kg': 0.02 * attendee_count   # 20g per person
        })
        
        for material, quantity in materials.items():
            if material in ['paper_kg', 'plastic_kg', 'fabric_kg']:
                material_type = material.replace('_kg', '')
                total_co2 += quantity * self.EMISSION_FACTORS['materials'][f'{material_type}_per_kg']
        
        # Digital alternatives reduction
        digital_adoption = event_data.get('digital_adoption_ratio', 0.5)
        total_co2 *= (1 - digital_adoption * (1 - self.EMISSION_FACTORS['materials']['digital_alternative_reduction']))
        
        return total_co2
    
    def calculate_waste_footprint(self, event_data: Dict) -> float:
        """Calculate waste carbon footprint"""
        total_co2 = 0.0
        attendee_count = event_data.get('expected_attendees', 0)
        
        # Waste generation (kg per person)
        waste_per_person = event_data.get('waste_per_person_kg', 2.0)
        total_waste = attendee_count * waste_per_person
        
        # Waste management distribution
        waste_management = event_data.get('waste_management', {
            'landfill': 0.4,
            'recycling': 0.4,
            'composting': 0.2
        })
        
        for method, ratio in waste_management.items():
            waste_amount = total_waste * ratio
            total_co2 += waste_amount * self.EMISSION_FACTORS['waste'][f'{method}_per_kg']
        
        # Food waste
        food_waste_kg = event_data.get('food_waste_kg', attendee_count * 0.5)  # 500g per person
        total_co2 += food_waste_kg * self.EMISSION_FACTORS['waste']['food_waste_per_kg']
        
        return total_co2
    
    def calculate_accommodation_footprint(self, event_data: Dict) -> float:
        """Calculate accommodation carbon footprint"""
        total_co2 = 0.0
        
        # Attendees needing accommodation
        accommodation_needed = event_data.get('attendees_needing_accommodation', 0)
        if accommodation_needed == 0:
            return 0.0
        
        # Accommodation types
        accommodation_types = event_data.get('accommodation_types', {
            'hotel': 0.6,
            'hostel': 0.2,
            'airbnb': 0.2
        })
        
        # Average nights
        avg_nights = event_data.get('avg_accommodation_nights', 2)
        
        for accom_type, ratio in accommodation_types.items():
            guests = accommodation_needed * ratio
            total_co2 += guests * avg_nights * self.EMISSION_FACTORS['accommodation'][f'{accom_type}_per_night_per_room']
        
        # Green certification reduction
        if event_data.get('green_accommodation_ratio', 0) > 0:
            green_ratio = event_data['green_accommodation_ratio']
            total_co2 *= (1 - green_ratio * (1 - self.EMISSION_FACTORS['accommodation']['green_certified_reduction']))
        
        return total_co2
    
    def calculate_digital_footprint(self, event_data: Dict) -> float:
        """Calculate digital services carbon footprint"""
        total_co2 = 0.0
        
        # Virtual/hybrid event components
        if event_data.get('is_virtual') or event_data.get('is_hybrid'):
            attendee_count = event_data.get('expected_attendees', 0)
            virtual_attendees = attendee_count if event_data.get('is_virtual') else \
                               attendee_count * event_data.get('virtual_attendance_ratio', 0.3)
            
            event_duration_hours = event_data.get('duration_hours', 8)
            
            # Video streaming/conferencing
            if event_data.get('has_live_streaming'):
                total_co2 += virtual_attendees * event_duration_hours * \
                           self.EMISSION_FACTORS['digital']['streaming_per_hour_per_person']
            else:
                total_co2 += virtual_attendees * event_duration_hours * \
                           self.EMISSION_FACTORS['digital']['video_conference_per_hour_per_person']
        
        # Email communications
        email_count = event_data.get('total_emails_sent', 0)
        total_co2 += email_count * self.EMISSION_FACTORS['digital']['email_per_message']
        
        # Cloud storage
        cloud_storage_gb = event_data.get('cloud_storage_gb', 10)
        storage_months = event_data.get('storage_duration_months', 6)
        total_co2 += cloud_storage_gb * storage_months * self.EMISSION_FACTORS['digital']['cloud_storage_per_gb_per_month']
        
        return total_co2
    
    def calculate_total_footprint(self, event_data: Dict) -> CarbonFootprint:
        """Calculate total carbon footprint for an event"""
        
        # Calculate footprint by category
        transportation_co2 = self.calculate_transportation_footprint(event_data)
        venue_co2 = self.calculate_venue_footprint(event_data)
        catering_co2 = self.calculate_catering_footprint(event_data)
        materials_co2 = self.calculate_materials_footprint(event_data)
        waste_co2 = self.calculate_waste_footprint(event_data)
        accommodation_co2 = self.calculate_accommodation_footprint(event_data)
        digital_co2 = self.calculate_digital_footprint(event_data)
        
        # Category breakdown
        category_breakdown = {
            'transportation': transportation_co2,
            'venue': venue_co2,
            'catering': catering_co2,
            'materials': materials_co2,
            'waste': waste_co2,
            'accommodation': accommodation_co2,
            'digital': digital_co2
        }
        
        # Total footprint
        total_co2 = sum(category_breakdown.values())
        
        # Per attendee calculation
        attendee_count = max(event_data.get('expected_attendees', 1), 1)
        per_attendee_co2 = total_co2 / attendee_count
        
        # Impact level assessment
        impact_level = self._assess_impact_level(per_attendee_co2)
        
        # Comparison data
        comparison_data = self._generate_comparison_data(total_co2, attendee_count, event_data)
        
        # Reduction potential
        reduction_potential = self._calculate_reduction_potential(category_breakdown, event_data)
        
        return CarbonFootprint(
            total_co2_kg=total_co2,
            category_breakdown=category_breakdown,
            per_attendee_kg=per_attendee_co2,
            comparison_data=comparison_data,
            impact_level=impact_level,
            reduction_potential=reduction_potential
        )
    
    def _assess_impact_level(self, per_attendee_co2: float) -> ImpactLevel:
        """Assess the environmental impact level"""
        if per_attendee_co2 < 5:
            return ImpactLevel.VERY_LOW
        elif per_attendee_co2 < 15:
            return ImpactLevel.LOW
        elif per_attendee_co2 < 30:
            return ImpactLevel.MEDIUM
        elif per_attendee_co2 < 60:
            return ImpactLevel.HIGH
        else:
            return ImpactLevel.VERY_HIGH
    
    def _generate_comparison_data(self, total_co2: float, attendee_count: int, event_data: Dict) -> Dict[str, Any]:
        """Generate comparison data for context"""
        per_attendee = total_co2 / attendee_count
        
        return {
            'equivalent_car_km': total_co2 / 0.12,  # Equivalent car kilometers
            'equivalent_tree_months': total_co2 / 22,  # Trees needed to absorb CO2 for 1 month
            'average_person_daily_footprint': per_attendee / 16.4,  # Average daily footprint
            'industry_average_per_attendee': {
                'conference': 25.0,
                'workshop': 8.0,
                'concert': 15.0,
                'exhibition': 35.0
            }.get(event_data.get('event_type', 'conference').lower(), 20.0),
            'percentage_of_annual_budget': (per_attendee / 4000) * 100  # % of average annual carbon budget
        }
    
    def _calculate_reduction_potential(self, breakdown: Dict[str, float], event_data: Dict) -> float:
        """Calculate potential CO2 reduction with optimizations"""
        potential_reductions = {
            'transportation': 0.6,  # 60% reduction with better transport
            'venue': 0.4,  # 40% reduction with green energy
            'catering': 0.5,  # 50% reduction with plant-based options
            'materials': 0.8,  # 80% reduction with digital alternatives
            'waste': 0.7,  # 70% reduction with better waste management
            'accommodation': 0.3,  # 30% reduction with green hotels
            'digital': 0.2   # 20% reduction with optimized streaming
        }
        
        total_potential = 0
        for category, emissions in breakdown.items():
            if category in potential_reductions:
                total_potential += emissions * potential_reductions[category]
        
        return total_potential

class SustainabilityRecommendationEngine:
    """AI-powered sustainability recommendation engine"""
    
    def __init__(self):
        self.calculator = CarbonFootprintCalculator()
    
    def generate_recommendations(self, event_data: Dict, carbon_footprint: CarbonFootprint) -> List[SustainabilityRecommendation]:
        """Generate personalized sustainability recommendations"""
        recommendations = []
        
        # Analyze each category and generate recommendations
        breakdown = carbon_footprint.category_breakdown
        
        # Transportation recommendations
        if breakdown['transportation'] > 0:
            recommendations.extend(self._get_transportation_recommendations(event_data, breakdown['transportation']))
        
        # Venue recommendations
        recommendations.extend(self._get_venue_recommendations(event_data, breakdown['venue']))
        
        # Catering recommendations
        recommendations.extend(self._get_catering_recommendations(event_data, breakdown['catering']))
        
        # Materials recommendations
        recommendations.extend(self._get_materials_recommendations(event_data, breakdown['materials']))
        
        # Waste management recommendations
        recommendations.extend(self._get_waste_recommendations(event_data, breakdown['waste']))
        
        # Sort by impact potential
        recommendations.sort(key=lambda x: x.impact_reduction, reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _get_transportation_recommendations(self, event_data: Dict, transport_emissions: float) -> List[SustainabilityRecommendation]:
        """Generate transportation recommendations"""
        recommendations = []
        
        # Public transport incentives
        if event_data.get('transport_modes', {}).get('car', 0) > 0.3:
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.TRANSPORTATION,
                title="Promote Public Transportation",
                description="Offer discounted or free public transport tickets to attendees",
                impact_reduction=transport_emissions * 0.3,
                cost_impact="increase",
                difficulty="easy",
                implementation_steps=[
                    "Partner with local transit authority",
                    "Include transit vouchers in registration",
                    "Provide clear public transport directions",
                    "Set up shuttle services from major transit hubs"
                ],
                estimated_savings={
                    'co2_kg': transport_emissions * 0.3,
                    'cost_per_attendee': -5.0  # Additional cost
                }
            ))
        
        # Virtual/hybrid option
        if not event_data.get('is_virtual') and not event_data.get('is_hybrid'):
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.TRANSPORTATION,
                title="Add Virtual Attendance Option",
                description="Offer hybrid attendance to reduce travel-related emissions",
                impact_reduction=transport_emissions * 0.4,
                cost_impact="neutral",
                difficulty="moderate",
                implementation_steps=[
                    "Set up live streaming infrastructure",
                    "Create virtual networking spaces",
                    "Offer digital swag bags",
                    "Enable virtual Q&A participation"
                ],
                estimated_savings={
                    'co2_kg': transport_emissions * 0.4,
                    'cost_per_attendee': 2.0  # Slight savings
                }
            ))
        
        # Carbon offset program
        recommendations.append(SustainabilityRecommendation(
            category=SustainabilityCategory.TRANSPORTATION,
            title="Implement Carbon Offset Program",
            description="Purchase carbon offsets for unavoidable travel emissions",
            impact_reduction=transport_emissions * 0.8,
            cost_impact="increase",
            difficulty="easy",
            implementation_steps=[
                "Calculate total travel emissions",
                "Purchase certified carbon offsets",
                "Communicate offset program to attendees",
                "Display offset certificates at event"
            ],
            estimated_savings={
                'co2_kg': transport_emissions * 0.8,
                'cost_per_attendee': -3.0
            }
        ))
        
        return recommendations
    
    def _get_venue_recommendations(self, event_data: Dict, venue_emissions: float) -> List[SustainabilityRecommendation]:
        """Generate venue recommendations"""
        recommendations = []
        
        # Green energy
        if event_data.get('energy_source', 'grid') != 'renewable':
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.VENUE,
                title="Switch to Renewable Energy",
                description="Use venues powered by renewable energy or purchase green energy certificates",
                impact_reduction=venue_emissions * 0.6,
                cost_impact="neutral",
                difficulty="moderate",
                implementation_steps=[
                    "Research venues with renewable energy",
                    "Purchase renewable energy certificates",
                    "Install temporary solar panels if possible",
                    "Use energy-efficient equipment"
                ],
                estimated_savings={
                    'co2_kg': venue_emissions * 0.6,
                    'cost_per_attendee': 1.0
                }
            ))
        
        # Energy efficiency
        recommendations.append(SustainabilityRecommendation(
            category=SustainabilityCategory.VENUE,
            title="Optimize Energy Usage",
            description="Implement energy-saving measures during the event",
            impact_reduction=venue_emissions * 0.25,
            cost_impact="decrease",
            difficulty="easy",
            implementation_steps=[
                "Use LED lighting only",
                "Optimize HVAC settings",
                "Turn off equipment when not in use",
                "Use natural lighting when possible"
            ],
            estimated_savings={
                'co2_kg': venue_emissions * 0.25,
                'cost_per_attendee': 3.0
            }
        ))
        
        return recommendations
    
    def _get_catering_recommendations(self, event_data: Dict, catering_emissions: float) -> List[SustainabilityRecommendation]:
        """Generate catering recommendations"""
        recommendations = []
        
        # Plant-based options
        meat_ratio = event_data.get('meal_distribution', {}).get('meat_heavy', 0) + \
                    event_data.get('meal_distribution', {}).get('meat_moderate', 0)
        
        if meat_ratio > 0.5:
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.CATERING,
                title="Increase Plant-Based Menu Options",
                description="Reduce meat consumption by offering attractive vegetarian and vegan alternatives",
                impact_reduction=catering_emissions * 0.4,
                cost_impact="decrease",
                difficulty="easy",
                implementation_steps=[
                    "Partner with caterers specializing in plant-based cuisine",
                    "Make vegetarian the default option",
                    "Offer meat as an add-on choice",
                    "Highlight environmental benefits on menu"
                ],
                estimated_savings={
                    'co2_kg': catering_emissions * 0.4,
                    'cost_per_attendee': 4.0
                }
            ))
        
        # Local sourcing
        if event_data.get('local_sourcing_ratio', 0) < 0.7:
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.CATERING,
                title="Source Food Locally",
                description="Partner with local farms and suppliers to reduce food miles",
                impact_reduction=catering_emissions * 0.2,
                cost_impact="neutral",
                difficulty="moderate",
                implementation_steps=[
                    "Research local organic farms",
                    "Partner with farm-to-table caterers",
                    "Feature local specialties on menu",
                    "Display supplier information at event"
                ],
                estimated_savings={
                    'co2_kg': catering_emissions * 0.2,
                    'cost_per_attendee': 0.0
                }
            ))
        
        return recommendations
    
    def _get_materials_recommendations(self, event_data: Dict, materials_emissions: float) -> List[SustainabilityRecommendation]:
        """Generate materials recommendations"""
        recommendations = []
        
        # Digital alternatives
        digital_adoption = event_data.get('digital_adoption_ratio', 0.5)
        if digital_adoption < 0.8:
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.MATERIALS,
                title="Go Paperless",
                description="Replace printed materials with digital alternatives",
                impact_reduction=materials_emissions * 0.7,
                cost_impact="decrease",
                difficulty="easy",
                implementation_steps=[
                    "Create event app with all information",
                    "Use QR codes for session materials",
                    "Send digital receipts and certificates",
                    "Provide USB drives instead of folders"
                ],
                estimated_savings={
                    'co2_kg': materials_emissions * 0.7,
                    'cost_per_attendee': 8.0
                }
            ))
        
        # Sustainable swag
        recommendations.append(SustainabilityRecommendation(
            category=SustainabilityCategory.MATERIALS,
            title="Choose Eco-Friendly Swag",
            description="Select promotional items made from sustainable materials",
            impact_reduction=materials_emissions * 0.3,
            cost_impact="neutral",
            difficulty="easy",
            implementation_steps=[
                "Choose items made from recycled materials",
                "Select reusable products (water bottles, bags)",
                "Avoid single-use plastic items",
                "Partner with sustainable merchandise suppliers"
            ],
            estimated_savings={
                'co2_kg': materials_emissions * 0.3,
                'cost_per_attendee': 0.0
            }
        ))
        
        return recommendations
    
    def _get_waste_recommendations(self, event_data: Dict, waste_emissions: float) -> List[SustainabilityRecommendation]:
        """Generate waste management recommendations"""
        recommendations = []
        
        # Improve recycling
        recycling_ratio = event_data.get('waste_management', {}).get('recycling', 0.4)
        if recycling_ratio < 0.7:
            recommendations.append(SustainabilityRecommendation(
                category=SustainabilityCategory.WASTE,
                title="Enhance Recycling Program",
                description="Set up comprehensive recycling and composting stations",
                impact_reduction=waste_emissions * 0.5,
                cost_impact="neutral",
                difficulty="easy",
                implementation_steps=[
                    "Place clearly labeled recycling bins throughout venue",
                    "Set up composting stations for food waste",
                    "Train staff on waste sorting",
                    "Partner with local recycling facilities"
                ],
                estimated_savings={
                    'co2_kg': waste_emissions * 0.5,
                    'cost_per_attendee': 1.0
                }
            ))
        
        # Zero waste goal
        recommendations.append(SustainabilityRecommendation(
            category=SustainabilityCategory.WASTE,
            title="Aim for Zero Waste Event",
            description="Implement comprehensive waste reduction strategies",
            impact_reduction=waste_emissions * 0.8,
            cost_impact="neutral",
            difficulty="challenging",
            implementation_steps=[
                "Eliminate single-use items",
                "Use reusable plates, cups, and utensils",
                "Set up donation stations for leftover items",
                "Measure and track waste production"
            ],
            estimated_savings={
                'co2_kg': waste_emissions * 0.8,
                'cost_per_attendee': 2.0
            }
        ))
        
        return recommendations

class SustainabilityTracker:
    """Main sustainability tracking system"""
    
    def __init__(self):
        self.calculator = CarbonFootprintCalculator()
        self.recommendation_engine = SustainabilityRecommendationEngine()
    
    def analyze_event_sustainability(self, event_id: int, event_data: Dict) -> SustainabilityMetrics:
        """Perform comprehensive sustainability analysis"""
        
        # Calculate carbon footprint
        carbon_footprint = self.calculator.calculate_total_footprint(event_data)
        
        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(event_data, carbon_footprint)
        
        # Calculate sustainability score
        sustainability_score = self._calculate_sustainability_score(event_data, carbon_footprint)
        
        # Assess achieved goals
        goals_achieved = self._assess_sustainability_goals(event_data, carbon_footprint)
        
        # Determine green badges
        green_badges = self._determine_green_badges(event_data, carbon_footprint, goals_achieved)
        
        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(carbon_footprint, recommendations)
        
        # Store results in database
        self._store_sustainability_metrics(event_id, carbon_footprint, sustainability_score)
        
        return SustainabilityMetrics(
            carbon_footprint=carbon_footprint,
            sustainability_score=sustainability_score,
            goals_achieved=goals_achieved,
            recommendations=recommendations,
            green_badges=green_badges,
            improvement_areas=improvement_areas
        )
    
    def _calculate_sustainability_score(self, event_data: Dict, carbon_footprint: CarbonFootprint) -> float:
        """Calculate overall sustainability score (0-100)"""
        base_score = 50  # Start with neutral score
        
        # Adjust based on per-attendee emissions
        per_attendee = carbon_footprint.per_attendee_kg
        
        if per_attendee < 5:
            emission_score = 40
        elif per_attendee < 15:
            emission_score = 30
        elif per_attendee < 30:
            emission_score = 20
        elif per_attendee < 60:
            emission_score = 10
        else:
            emission_score = 0
        
        # Bonus points for sustainable practices
        bonus_points = 0
        
        # Digital adoption
        digital_adoption = event_data.get('digital_adoption_ratio', 0.5)
        bonus_points += digital_adoption * 10
        
        # Renewable energy
        if event_data.get('energy_source') == 'renewable':
            bonus_points += 15
        elif event_data.get('energy_source') == 'mixed':
            bonus_points += 8
        
        # Plant-based catering
        veg_ratio = event_data.get('meal_distribution', {}).get('vegetarian', 0) + \
                   event_data.get('meal_distribution', {}).get('vegan', 0)
        bonus_points += veg_ratio * 10
        
        # Local sourcing
        local_ratio = event_data.get('local_sourcing_ratio', 0)
        bonus_points += local_ratio * 8
        
        # Waste management
        recycling_ratio = event_data.get('waste_management', {}).get('recycling', 0.4) + \
                         event_data.get('waste_management', {}).get('composting', 0.2)
        bonus_points += recycling_ratio * 12
        
        # Virtual/hybrid options
        if event_data.get('is_virtual'):
            bonus_points += 20
        elif event_data.get('is_hybrid'):
            bonus_points += 10
        
        total_score = min(100, base_score + emission_score + bonus_points)
        return max(0, total_score)
    
    def _assess_sustainability_goals(self, event_data: Dict, carbon_footprint: CarbonFootprint) -> List[SustainabilityGoal]:
        """Assess which sustainability goals have been achieved"""
        achieved_goals = []
        
        # Carbon neutral goal
        if carbon_footprint.per_attendee_kg < 5 or event_data.get('carbon_offset_purchased'):
            achieved_goals.append(SustainabilityGoal.CARBON_NEUTRAL)
        
        # Waste free goal
        landfill_ratio = event_data.get('waste_management', {}).get('landfill', 0.4)
        if landfill_ratio < 0.1:
            achieved_goals.append(SustainabilityGoal.WASTE_FREE)
        
        # Local sourcing goal
        if event_data.get('local_sourcing_ratio', 0) > 0.8:
            achieved_goals.append(SustainabilityGoal.LOCAL_SOURCING)
        
        # Renewable energy goal
        if event_data.get('energy_source') == 'renewable':
            achieved_goals.append(SustainabilityGoal.RENEWABLE_ENERGY)
        
        # Sustainable transport goal
        car_ratio = event_data.get('transport_modes', {}).get('car', 0.4)
        if car_ratio < 0.2:
            achieved_goals.append(SustainabilityGoal.SUSTAINABLE_TRANSPORT)
        
        # Eco-friendly materials goal
        if event_data.get('digital_adoption_ratio', 0.5) > 0.8:
            achieved_goals.append(SustainabilityGoal.ECO_FRIENDLY_MATERIALS)
        
        return achieved_goals
    
    def _determine_green_badges(self, event_data: Dict, carbon_footprint: CarbonFootprint, 
                               goals_achieved: List[SustainabilityGoal]) -> List[str]:
        """Determine green badges earned"""
        badges = []
        
        # Impact level badges
        if carbon_footprint.impact_level == ImpactLevel.VERY_LOW:
            badges.append("Ultra Low Carbon")
        elif carbon_footprint.impact_level == ImpactLevel.LOW:
            badges.append("Low Carbon Champion")
        
        # Goal-based badges
        if SustainabilityGoal.CARBON_NEUTRAL in goals_achieved:
            badges.append("Carbon Neutral Event")
        
        if SustainabilityGoal.WASTE_FREE in goals_achieved:
            badges.append("Zero Waste Hero")
        
        if SustainabilityGoal.LOCAL_SOURCING in goals_achieved:
            badges.append("Local Champion")
        
        # Special achievements
        if len(goals_achieved) >= 4:
            badges.append("Sustainability Leader")
        
        if event_data.get('is_virtual'):
            badges.append("Digital Pioneer")
        
        # Innovation badges
        if event_data.get('has_innovation_features'):
            badges.append("Green Innovator")
        
        return badges
    
    def _identify_improvement_areas(self, carbon_footprint: CarbonFootprint, 
                                   recommendations: List[SustainabilityRecommendation]) -> List[str]:
        """Identify key areas for improvement"""
        areas = []
        
        # Find highest emission categories
        breakdown = carbon_footprint.category_breakdown
        sorted_categories = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        
        # Top 3 emission sources
        for category, emissions in sorted_categories[:3]:
            if emissions > carbon_footprint.total_co2_kg * 0.1:  # More than 10% of total
                areas.append(category.replace('_', ' ').title())
        
        # Add recommendation-based areas
        for rec in recommendations[:3]:
            area = f"{rec.category.value.replace('_', ' ').title()} Optimization"
            if area not in areas:
                areas.append(area)
        
        return areas[:5]  # Return top 5 areas
    
    def _store_sustainability_metrics(self, event_id: int, carbon_footprint: CarbonFootprint, 
                                     sustainability_score: float):
        """Store sustainability metrics in database"""
        try:
            # Store in SustainabilityMetric model (to be created)
            # For now, store in EventAnalytics
            analytics = EventAnalytics.query.filter_by(event_id=event_id).first()
            if not analytics:
                analytics = EventAnalytics(event_id=event_id)
                db.session.add(analytics)
            
            # Store sustainability data (you might want to create a dedicated model)
            analytics.sustainability_score = sustainability_score
            analytics.carbon_footprint_kg = carbon_footprint.total_co2_kg
            analytics.updated_at = datetime.utcnow()
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Error storing sustainability metrics: {e}")

# Global instance
sustainability_tracker = SustainabilityTracker()

# Utility functions for easy access
def calculate_event_footprint(event_id: int, event_data: Dict) -> CarbonFootprint:
    """Calculate carbon footprint for an event"""
    calculator = CarbonFootprintCalculator()
    return calculator.calculate_total_footprint(event_data)

def get_sustainability_recommendations(event_data: Dict) -> List[SustainabilityRecommendation]:
    """Get sustainability recommendations for an event"""
    calculator = CarbonFootprintCalculator()
    recommendation_engine = SustainabilityRecommendationEngine()
    
    carbon_footprint = calculator.calculate_total_footprint(event_data)
    return recommendation_engine.generate_recommendations(event_data, carbon_footprint)

def analyze_event_sustainability(event_id: int, event_data: Dict) -> SustainabilityMetrics:
    """Perform full sustainability analysis"""
    return sustainability_tracker.analyze_event_sustainability(event_id, event_data)