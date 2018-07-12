#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod


class UsdaObject(ABC):
    """Describes any kind of USDA API result."""

    @staticmethod
    @abstractmethod
    def from_response_data(response_data):
        """Generate an object from JSON response data."""
        raise NotImplementedError


class Measure(UsdaObject):

    @staticmethod
    def from_response_data(response_data):
        return Measure(
            quantity=response_data["qty"],
            gram_equivalent=response_data["eqv"],
            label=response_data["label"],
            value=response_data["value"],
        )

    def __init__(self, quantity, gram_equivalent, label, value):
        super().__init__()
        self.quantity = float(quantity)
        self.gram_equivalent = float(gram_equivalent)
        self.label = str(label)
        self.value = float(value)

    def __repr__(self):
        return "Measure '{0}': {1} {2}".format(
            self.label, self.value, self.quantity)

    def __str__(self):
        return self.label


class Nutrient(UsdaObject):
    """Describes a USDA nutrient.
    In reports, can hold associated measurement data."""

    @staticmethod
    def from_response_data(response_data):
        return Nutrient(id=response_data['id'], name=response_data['name'])

    def __init__(self, id, name,
                 group=None, unit=None, value=None, measures=None):
        super().__init__()
        self.id = int(id)
        self.name = str(name)
        self.group = str(group) if group is not None else None
        self.unit = str(unit) if unit is not None else None
        self.value = float(value) if value is not None else None
        self.measures = measures

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Nutrient ID {0} '{1}'".format(self.id, self.name)


class Food(UsdaObject):
    """Describes a USDA food item."""

    @staticmethod
    def from_response_data(response_data):
        return Food(
            id=response_data['id']
            if 'id' in response_data
            else response_data['ndbno'],
            name=response_data['name'],
        )

    def __init__(self, id, name):
        super().__init__()
        self.id = int(id)
        self.name = str(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Food ID {0} '{1}'".format(self.id, self.name)


class FoodReport(UsdaObject):
    """Describes a USDA food report."""

    @staticmethod
    def _get_measures(raw_measures):
        """Get measurements from JSON data."""
        return list(map(Measure.from_response_data, raw_measures))

    @staticmethod
    def _get_nutrients(raw_nutrients):
        """Get nutrients from JSON data with their associated measurements."""
        return [
            Nutrient(
                id=raw_nutrient["nutrient_id"],
                name=raw_nutrient["name"],
                group=raw_nutrient["group"],
                unit=raw_nutrient["unit"],
                value=raw_nutrient["value"],
                measures=FoodReport._get_measures(raw_nutrient["measures"]),
            )
            for raw_nutrient in raw_nutrients
        ]

    @staticmethod
    def from_response_data(response_data):
        report = response_data["report"]
        type = report["type"]
        food = report['food']
        food_group = None if type == "Basic" or type == "Statistics" \
            else food["fg"]
        return FoodReport(
            food=Food.from_response_data(food),
            nutrients=FoodReport._get_nutrients(food["nutrients"]),
            report_type=report["type"],
            foot_notes=report["footnotes"],
            food_group=food_group,
        )

    def __init__(self, food, nutrients, report_type, foot_notes, food_group):
        super().__init__()
        assert isinstance(food, Food)
        self.food = food
        self.nutrients = nutrients
        self.report_type = str(report_type)
        self.foot_notes = foot_notes
        self.food_group = str(food_group) if food_group is not None else None

    def __repr__(self):
        return "Food Report for '{0}'".format(repr(self.food))


class NutrientReport(UsdaObject):
    """Describes a USDA nutrient report."""

    def __init__(self, foods):
        super().__init__()
        assert all(
            isinstance(food, Food) and all(
                isinstance(nutrient, Nutrient)
                for nutrient in nutrients
            )
            for food, nutrients in foods.items()
        )
        self.foods = foods

    @staticmethod
    def from_response_data(response_data):
        report = response_data["report"]
        return NutrientReport({
            Food.from_response_data(food): [
                Nutrient(
                    id=nutrient["nutrient_id"],
                    name=nutrient["nutrient"],
                    unit=nutrient["unit"],
                    value=nutrient["value"],
                    measures=[
                        Measure(
                            quantity=food["weight"],
                            gram_equivalent=nutrient["gm"],
                            label=food["measure"],
                            value=nutrient["value"],
                        )
                    ],
                )
                for nutrient in food["nutrients"]
            ]
            for food in report["foods"]
        })
