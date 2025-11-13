# HSMAIET-Backend

# Run Application on dev server
clear && docker-compose -f docker-compose-local.yml down
clear && docker-compose -f docker-compose-local.yml up

# When changes made with YML file 
clear && docker-compose -f docker-compose-local.yml up --build