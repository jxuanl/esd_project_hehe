DROP SCHEMA IF EXISTS drink_ingredients;

create schema drink_ingredients;

use drink_ingredients;

create table drink_ingredients
(drink_ingredient_id int not null auto_increment,
drink_id int,
ingredient varchar(255) not null,
quantity int not null,
unit varchar(15) not null,
constraint drink_ingredient_id_pk primary key (drink_ingredient_id));

insert into drink_ingredients (drink_ingredient_id, drink_id, ingredient, quantity, unit)
values 
	-- Espresso (Drink ID 1)
    (16, 1, 'Coffee Beans', 10, 'g'),

    -- Latte (Drink ID 2)
    (16, 2, 'Coffee Beans', 1, 'shot'),
    -- (18, 2, 'Regular Milk', 200, 'ml'),

    -- Cappuccino (Drink ID 3)
    (16, 3, 'Coffee Beans', 1, 'shot'),
    -- (104, 3, 'Regular Milk', 100, 'ml'),

    -- Americano (Drink ID 4)
	(16, 4, 'Coffee Beans', 10, 'g'),

    -- Iced Matcha Latte (Drink ID 5)
    (24, 5, 'Matcha Powder', 5, 'g'),
	(20, 5, 'Sugar Syrup', 1, 'tbsp'),
    -- (18, 5, 'Regular Milk', 180, 'ml'),

    -- Iced Chocolate (Drink ID 6)
    (26, 6, 'Chocolate Syrup', 2, 'tbsp'),
    -- (18, 6, 'Regular Milk', 200, 'ml');
	-- (31, 2, "Chocolate Sprinkles", 4, 'g'),
	-- (40, 6, 'Whipped Cream', 20, 'g');;

	-- no drink ids
	(104, 'Regular Milk', 200, 'ml'),
	(105, 'Skim Milk', 200, 'ml'),
	(106, 'Almond Milk', 200, 'ml'),
	(107, 'Oat Milk', 200, 'ml'),
	(108, 'Soy Milk', 200, 'ml'),
	(109, 'Vanilla Syrup', 2, 'tbsp'),
	(110, 'Caramel Syrup', 2, 'tbsp'),
	(111, 'Hazelnut Syrup', 2, 'tbsp'),
	(112, 'Whipped Cream', 20, 'g'),
	(113, 'Chocolate Sprinkles', 4, 'g');
    

select * from drink_ingredients;