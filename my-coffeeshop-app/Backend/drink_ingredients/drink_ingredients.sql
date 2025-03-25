create schema drink_ingredients;

-- drop schema drink_ingredients;

use drink_ingredients;

create table drink_ingredients
(drink_ingredient_id int not null auto_increment,
drink_id int not null ,
ingredient_id int not null,
quantity int not null,
unit varchar(15) not null,
constraint drink_ingredient_id_pk primary key (drink_ingredient_id),
constraint drink_id_fk foreign key (drink_id) references drink_menu(drink_id));

insert into drink_ingredients (drink_ingredient_id, drink_id, ingredient_id, quantity, unit)
values 
	(1, 1, 3, 2, 'ounces'),
	(2, 2, 4, 100, 'ml');
    

select * from drink_ingredients;