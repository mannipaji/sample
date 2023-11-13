SELECT
  distinct
  customer_id,
  first_name,
  last_name,
  gender,
  phone_number,
  email_id,
  birth_date,
  cast(age as int) as age,
  education_level,
  marital_status,
  cast(number_of_children as int) as number_of_children,
  register_date,
  occupation,
  annual_income,
  hobbies,
  degree_of_loyalty,
  social_class,
  mailing_street,
  city,
  state,
  country,
  zip_code
FROM
customer