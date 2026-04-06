
CREATE TABLE public.category
(
    id_category integer NOT NULL DEFAULT 1,
    name_category text NOT NULL,
    code text,
    isEntry boolean DEFAULT TRUE,
    isOut boolean DEFAULT TRUE,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT category_pkey PRIMARY KEY (id_category)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.category
    OWNER to postgres;



CREATE SEQUENCE public.category_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.category_id_seq
    OWNED BY public.category.id_category;

ALTER SEQUENCE public.category_id_seq
    OWNER TO postgres;



ALTER TABLE IF EXISTS public.category
    ALTER COLUMN id_category SET DEFAULT nextval('category_id_seq'::regclass);



----------------------------------------------------


CREATE TABLE public.unity_weight
(
    id_unity integer NOT NULL DEFAULT 1,
    name text NOT NULL,
    code text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT unity_weight_pkey PRIMARY KEY (id_unity)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.unity_weight
    OWNER to postgres;


CREATE SEQUENCE public.unity_weight_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.unity_weight_id_seq
    OWNED BY public.unity_weight.id_unity;

ALTER SEQUENCE public.unity_weight_id_seq
    OWNER TO postgres;

ALTER TABLE IF EXISTS public.unity_weight
    ALTER COLUMN id_unity SET DEFAULT nextval('unity_weight_id_seq'::regclass);


------------------------------------------------------------------------------------------

CREATE TABLE public.logbook_entry
(
    id_logbook_entry integer NOT NULL DEFAULT 1,
    unity_id integer NOT NULL,
    category_id integer NOT NULL,
    logbook_out_id integer,
    shipping_guide text,
    description text,
    quantity integer NOT NULL,
    weight integer,
    provider text,
    truck_license text,
    name_driver text,
    destiny_intern text,
    authorized_by text,
    lat text,
    long text,
    observations text,
    name_user text,
    workday text,
    status text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by text NOT NULL,
    updated_by text NOT NULL,
    CONSTRAINT logbook_entry_pkey PRIMARY KEY (id_logbook_entry),
    CONSTRAINT logbook_entry_unity_id_fkey FOREIGN KEY (unity_id)
        REFERENCES public.unity_weight (id_unity) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT logbook_entry_category_id_fkey FOREIGN KEY (category_id)
        REFERENCES public.category (id_category) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT logbook_entry_out_id_fkey FOREIGN KEY (logbook_out_id)
        REFERENCES public.logbook_out (id_logbook_out) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.logbook_entry
    OWNER to postgres;


CREATE SEQUENCE public.logbook_entry_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.logbook_entry_id_seq
    OWNED BY public.logbook_entry.id_logbook_entry;

ALTER SEQUENCE public.logbook_entry_id_seq
    OWNER TO postgres;

ALTER TABLE IF EXISTS public.logbook_entry
    ALTER COLUMN id_logbook_entry SET DEFAULT nextval('logbook_entry_id_seq'::regclass);


-----------------------------------------------------------------------------------------------------------------------

CREATE TABLE public.logbook_out
(
    id_logbook_out integer NOT NULL DEFAULT 1,
    unity_id integer NOT NULL,
    category_id integer NOT NULL,
    shipping_guide text,
    quantity integer,
    weight integer,
    truck_license text,
    name_driver text,
    person_withdraws text,
    destiny text,
    lat text,
    long text,
    authorized_by text,
    observations text,
    workday text,
    name_user text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by text NOT NULL,
    updated_by text NOT NULL,
    CONSTRAINT logbook_out_pkey PRIMARY KEY (id_logbook_out),
    CONSTRAINT logbook_out_unity_id_fkey FOREIGN KEY (unity_id)
        REFERENCES public.unity_weight (id_unity) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT logbook_out_category_id_fkey FOREIGN KEY (category_id)
        REFERENCES public.category (id_category) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.logbook_out
    OWNER to nextgen;


CREATE SEQUENCE public.logbook_out_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.logbook_out_id_seq
    OWNED BY public.logbook_out.id_logbook_out;

ALTER SEQUENCE public.logbook_out_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.logbook_out
    ALTER COLUMN id_logbook_out SET DEFAULT nextval('logbook_out_id_seq'::regclass);

-----------------------------------------------------------------------------------------

CREATE TABLE public.sector
(
    id_sector integer NOT NULL DEFAULT 1,
    name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT sector_pkey PRIMARY KEY (id_sector)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.sector
    OWNER to nextgen;

CREATE SEQUENCE public.sector_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.sector_id_seq
    OWNED BY public.sector.id_sector;

ALTER SEQUENCE public.sector_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.sector
    ALTER COLUMN id_sector SET DEFAULT nextval('sector_id_seq'::regclass);


-----------------------------------------------------------------------------------------

CREATE TABLE public.business
(
    id_business integer NOT NULL DEFAULT 1,
    name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT business_pkey PRIMARY KEY (id_business)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.business
    OWNER to nextgen;


CREATE SEQUENCE public.business_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.business_id_seq
    OWNED BY public.business.id_business;

ALTER SEQUENCE public.business_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.business
    ALTER COLUMN id_business SET DEFAULT nextval('business_id_seq'::regclass);


-----------------------------------------------------------------------------------------

CREATE TABLE public.group_business
(
    id_group_business integer NOT NULL DEFAULT 1,
    sector_id integer NOT NULL,
    name text NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT group_business_pkey PRIMARY KEY (id_group_business),
    CONSTRAINT group_business_sector_id_fkey FOREIGN KEY (sector_id)
        REFERENCES public.sector (id_sector) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT group_business_business_id_fkey FOREIGN KEY (business_id)
        REFERENCES public.business (id_business) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.group_business
    OWNER to nextgen;


CREATE SEQUENCE public.group_business_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.group_business_id_seq
    OWNED BY public.group_business.id_group_business;

ALTER SEQUENCE public.group_business_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.group_business
    ALTER COLUMN id_group_business SET DEFAULT nextval('group_business_id_seq'::regclass);


---------------------------UPDATE LOGBOOK ENTRY---------------------------------
ALTER TABLE IF EXISTS public.logbook_entry
    ADD COLUMN group_business_id integer NOT NULL;
ALTER TABLE IF EXISTS public.logbook_entry
    ADD CONSTRAINT logbook_entry_group_business_id_fkey FOREIGN KEY (group_business_id)
    REFERENCES public.group_business (id_group_business) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS fki_logbook_entry_group_business_id_fkey
    ON public.logbook_entry(group_business_id);

---------------------------UPDATE LOGBOOK OUT---------------------------------
ALTER TABLE IF EXISTS public.logbook_out
    ADD COLUMN group_business_id integer NOT NULL;
ALTER TABLE IF EXISTS public.logbook_out
    ADD CONSTRAINT logbook_out_group_business_id_fkey FOREIGN KEY (group_business_id)
    REFERENCES public.group_business (id_group_business) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS fki_logbook_out_group_business_id_fkey
    ON public.logbook_out(group_business_id);


---------------------------------------------------------------------------------

CREATE TABLE public.report_generated
(
    id_report integer NOT NULL DEFAULT 1,
    business_id integer NOT NULL,
    type_report text NOT NULL,
    status text,
    shipping_date timestamp without time zone,
    shipping_error text,
    created_at timestamp without time zone DEFAULT now(),
    deadline timestamp without time zone,
    start_date timestamp without time zone,
    created_by text,
    CONSTRAINT report_generated_pkey PRIMARY KEY (id_report),
    CONSTRAINT report_generated_business_id_fkey FOREIGN KEY (business_id)
        REFERENCES public.business (id_business) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.report_generated
    OWNER to nextgen;

CREATE SEQUENCE public.report_generated_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.report_generated_id_seq
    OWNED BY public.report_generated.id_report;

ALTER SEQUENCE public.report_generated_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.report_generated
    ALTER COLUMN id_report SET DEFAULT nextval('report_generated_id_seq'::regclass);

-------------------------------------------------------------------------------------------------------


CREATE TABLE public.logbook_images
(
    id_image integer NOT NULL DEFAULT 1,
    logbook_id_out integer,
    logbook_id_entry integer,
    image_path text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT logbook_images_pkey PRIMARY KEY (id_image),
    CONSTRAINT logbook_images_logbook_entry_id_fkey FOREIGN KEY (logbook_id_entry)
        REFERENCES public.logbook_entry (id_logbook_entry) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT logbook_images_logbook_out_id_fkey FOREIGN KEY (logbook_id_out)
        REFERENCES public.logbook_out (id_logbook_out) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.logbook_images
    OWNER to nextgen;


CREATE SEQUENCE public.logbook_images_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.logbook_images_id_seq
    OWNED BY public.logbook_images.id_image;

ALTER SEQUENCE public.logbook_images_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.logbook_images
    ALTER COLUMN id_image SET DEFAULT nextval('logbook_images_id_seq'::regclass);


--------------------------------------------------------------------------------------------

CREATE TABLE public.roles
(
    id_rol integer NOT NULL DEFAULT 1,
    name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT roles_pkey PRIMARY KEY (id_rol)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.roles
    OWNER to nextgen;



---------------------------------------------------------------------------------------

CREATE TABLE public.users
(
    id_user uuid NOT NULL DEFAULT gen_random_uuid(),
    "user" text NOT NULL,
    email text,
    password text NOT NULL,
    role_id uuid NOT NULL,
    attributes jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT users_pkey PRIMARY KEY (id_user),
    CONSTRAINT role_id_fkey FOREIGN KEY (role_id)
        REFERENCES public.roles (id_rol) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.users
    OWNER to nextgen;


-----------------------------------------------------------------------------------------------------------

CREATE TABLE public.permissions
(
    id_permission uuid NOT NULL DEFAULT gen_random_uuid(),
    name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT permissions_pkey PRIMARY KEY (id_permission)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.permissions
    OWNER to nextgen;

---------------------------------------------------------------------------------------------

CREATE TABLE public.role_permissions
(
    id_role_permission uuid NOT NULL DEFAULT gen_random_uuid(),
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT permission_rol_id_pk PRIMARY KEY (id_role_permission),
    CONSTRAINT role_id__fkey FOREIGN KEY (role_id)
        REFERENCES public.roles (id_rol) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT permission_id_fkey FOREIGN KEY (permission_id)
        REFERENCES public.permissions (id_permission) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.role_permissions
    OWNER to nextgen;


-----------------------------------------------------------------------------------------------


CREATE TABLE public.authorized
(
    id_authorized integer NOT NULL DEFAULT 1,
    name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT authorized_pkey PRIMARY KEY (id_authorized)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.authorized
    OWNER to nextgen;


CREATE SEQUENCE public.authorized_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.authorized_id_seq
    OWNED BY public.authorized.id_authorized;

ALTER SEQUENCE public.authorized_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.authorized
    ALTER COLUMN id_authorized SET DEFAULT nextval('authorized_id_seq'::regclass);



----------------------------------------------------------------------------------------------------------

CREATE TABLE public.destiny_intern
(
    id_destiny integer NOT NULL,
    name text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT destiny_intern_pkey PRIMARY KEY (id_destiny)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.destiny_intern
    OWNER to nextgen;


CREATE SEQUENCE public.destiny_intern_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.destiny_intern_id_seq
    OWNED BY public.destiny_intern.id_destiny;

ALTER SEQUENCE public.destiny_intern_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.destiny_intern
    ALTER COLUMN id_destiny SET DEFAULT nextval('destiny_intern_id_seq'::regclass);


----------------------------------------------------------------------------------------------------

CREATE TABLE public.request_idempotency
(
    id_request integer NOT NULL,
    uuid uuid NOT NULL UNIQUE,
    endpoint text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT request_idempotency_pkey PRIMARY KEY (id_request)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.request_idempotency
    OWNER to nextgen;

CREATE SEQUENCE public.request_idempotency_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.request_idempotency_id_seq
    OWNED BY public.request_idempotency.id_request;

ALTER SEQUENCE public.request_idempotency_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.request_idempotency
    ALTER COLUMN id_request SET DEFAULT nextval('request_idempotency_id_seq'::regclass);


--------------------------------------------------------------------------------------------------

CREATE TABLE public.dispatch_status
(
    id_status integer NOT NULL,
    name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT dispatch_status_pkey PRIMARY KEY (id_status)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dispatch_status
    OWNER to nextgen;


CREATE SEQUENCE public.dispatch_status_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.dispatch_status_id_seq
    OWNED BY public.dispatch_status.id_status;

ALTER SEQUENCE public.dispatch_status_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.dispatch_status
    ALTER COLUMN id_status SET DEFAULT nextval('dispatch_status_id_seq'::regclass);


--------------------------------------------------------------------------------------------------------------------------


CREATE TABLE public.dispatch_skus
(
    id_sku integer NOT NULL,
    type_sku text,
    code_sku text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by text,
    updated_by text,
    CONSTRAINT dispatch_skus_pkey PRIMARY KEY (id_sku)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dispatch_skus
    OWNER to nextgen;


CREATE SEQUENCE public.dispatch_skus_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.dispatch_skus_id_seq
    OWNED BY public.dispatch_skus.id_sku;

ALTER SEQUENCE public.dispatch_skus_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.dispatch_skus
    ALTER COLUMN id_sku SET DEFAULT nextval('dispatch_skus_id_seq'::regclass);


-------------------------------------------------------------------------------------------------------------------------


CREATE TABLE public.dispatch_products
(
    id_product integer NOT NULL,
    name text,
    price numeric,
    stock integer,
    presentation_type text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by text,
    updated_by text,
    CONSTRAINT dispatch_products_pkey PRIMARY KEY (id_product)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dispatch_products
    OWNER to nextgen;


CREATE SEQUENCE public.dispatch_products_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.dispatch_products_id_seq
    OWNED BY public.dispatch_products.id_product;

ALTER SEQUENCE public.dispatch_products_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.dispatch_products
    ALTER COLUMN id_product SET DEFAULT nextval('dispatch_products_id_seq'::regclass);


---------------------------------------------------------------------------------------------------------


CREATE TABLE public.products_sku
(
    id_product_sku integer NOT NULL,
    product_id integer,
    sku_id integer,
    quantity integer,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT products_sku_pkey PRIMARY KEY (id_product_sku),
    CONSTRAINT products_sku_product_id_fkey FOREIGN KEY (product_id)
        REFERENCES public.dispatch_products (id_product) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT products_sku_sku_id_fkey FOREIGN KEY (sku_id)
        REFERENCES public.dispatch_skus (id_sku) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;


ALTER TABLE IF EXISTS public.products_sku
    OWNER to nextgen;


CREATE SEQUENCE public.products_sku_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.products_sku_id_seq
    OWNED BY public.products_sku.id_product_sku;

ALTER SEQUENCE public.products_sku_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.products_sku
    ALTER COLUMN id_product_sku SET DEFAULT nextval('products_sku_id_seq'::regclass);



-------------------------------------------------------------------------------------------------------------

CREATE TABLE public.vehicle_type
(
    id_vehicle_type integer NOT NULL,
    name text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by text,
    updated_by text,
    CONSTRAINT vehicle_type_pkey PRIMARY KEY (id_vehicle_type)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.vehicle_type
    OWNER to nextgen;


CREATE SEQUENCE public.vehicle_type_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.vehicle_type_id_seq
    OWNED BY public.vehicle_type.id_vehicle_type;

ALTER SEQUENCE public.vehicle_type_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.vehicle_type
    ALTER COLUMN id_vehicle_type SET DEFAULT nextval('vehicle_type_id_seq'::regclass);


---------------------------------------------------------------------------------------------------------------------------

CREATE TABLE public.dispatch
(
    id_dispatch integer NOT NULL,
    destiny_id integer,
    vehicle_type_id integer,
    sku_id integer,
    driver text,
    observations text,
    status_id integer,
    truck_license text,
    weight integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    created_by text,
    updated_by text,
    CONSTRAINT dispatch_pkey PRIMARY KEY (id_dispatch),
    CONSTRAINT dispatch_status_id_fkey FOREIGN KEY (status_id)
        REFERENCES public.dispatch_status (id_status) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT dispatch_destiny_id_fkey FOREIGN KEY (destiny_id)
        REFERENCES public.destiny_intern (id_destiny) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT dispatch_vehicle_type_id_fkey FOREIGN KEY (vehicle_type_id)
        REFERENCES public.vehicle_type (id_vehicle_type) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
    CONSTRAINT dispatch_sku_id_fkey FOREIGN KEY (sku_id)
        REFERENCES public.dispatch_skus (id_sku) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dispatch
    OWNER to nextgen;


CREATE SEQUENCE public.dispatch_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.dispatch_id_seq
    OWNED BY public.dispatch.id_dispatch;

ALTER SEQUENCE public.dispatch_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.dispatch
    ALTER COLUMN id_dispatch SET DEFAULT nextval('dispatch_id_seq'::regclass);


------------------------------------------------------------------------------------------------


CREATE TABLE public.company_modules
(
    id_company_module integer NOT NULL,
    business_id integer NOT NULL,
    module_id integer,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT module_pkey PRIMARY KEY (id_company_module),
    CONSTRAINT company_modules_business_id_fkey FOREIGN KEY (business_id)
        REFERENCES public.business (id_business) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT company_modules_modules_id_fkey FOREIGN KEY (module_id)
        REFERENCES public.modules (id_module) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.company_modules
    OWNER to nextgen;


CREATE SEQUENCE public.company_modules_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.company_modules_id_seq
    OWNED BY public.company_modules.id_company_module;

ALTER SEQUENCE public.company_modules_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.company_modules
    ALTER COLUMN id_company_module SET DEFAULT nextval('company_modules_id_seq'::regclass);


---------------------------------------------------------------------------------------------

CREATE TABLE public.modules
(
    id_module integer NOT NULL,
    name text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT module_pkey PRIMARY KEY (id_module)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.modules
    OWNER to nextgen;


CREATE SEQUENCE public.modules_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.modules_id_seq
    OWNED BY public.modules.id_module;

ALTER SEQUENCE public.modules_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.modules
    ALTER COLUMN id_module SET DEFAULT nextval('modules_id_seq'::regclass);


--------------------------------------------------------------------------------------------------------

ALTER TABLE IF EXISTS public.permissions
    ADD COLUMN module_id integer;
ALTER TABLE IF EXISTS public.permissions
    ADD CONSTRAINT permission_module_id_fkey FOREIGN KEY (module_id)
    REFERENCES public.modules (id_module) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS fki_permission_module_id_fkey
    ON public.permissions(module_id);

------------------------------------------------------------------------------------------------------------

CREATE TABLE public.history_dispatch_status
(
    id_history_status integer NOT NULL,
    dispatch_id integer,
    previous_status_id integer,
    status_id integer,
    created_at timestamp without time zone DEFAULT now(),
    created_by text,
    CONSTRAINT history_dispatch_status_pkey PRIMARY KEY (id_history_status),
    CONSTRAINT history_dispatch_status_id_fkey FOREIGN KEY (status_id)
        REFERENCES public.dispatch_status (id_status) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT history_dispatch_dispatch_id_fkey FOREIGN KEY (dispatch_id)
        REFERENCES public.dispatch (id_dispatch) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT history_dispatch_previous_status_id_fkey FOREIGN KEY (previous_status_id)
        REFERENCES public.dispatch_status (id_status) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.history_dispatch_status
    OWNER to nextgen;


CREATE SEQUENCE public.history_dispatch_status_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.history_dispatch_status_id_seq
    OWNED BY public.history_dispatch_status.id_history_status;

ALTER SEQUENCE public.history_dispatch_status_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.history_dispatch_status
    ALTER COLUMN id_history_status SET DEFAULT nextval('history_dispatch_status_id_seq'::regclass);


-- Trigger y funcion para registrar el historial de cambios de los estados del despacho

CREATE OR REPLACE FUNCTION fn_log_dispatch_status()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO public.history_dispatch_status 
            (dispatch_id, previous_status_id, status_id, created_by)
        VALUES 
            (NEW.id_dispatch, NEW.status_id, NEW.status_id, NEW.created_by);

    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status_id IS DISTINCT FROM NEW.status_id THEN
            INSERT INTO public.history_dispatch_status 
                (dispatch_id, previous_status_id, status_id, created_by)
            VALUES 
                (NEW.id_dispatch, OLD.status_id, NEW.status_id, NEW.updated_by);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_dispatch_status_history
AFTER INSERT OR UPDATE ON public.dispatch
FOR EACH ROW
EXECUTE FUNCTION fn_log_dispatch_status();

--------------------------------------------------------------------------------------------------------------------


CREATE TABLE public.dispatch_reception
(
    id_reception integer NOT NULL,
    dispatch_id integer NOT NULL,
    is_correct boolean NOT NULL,
    observations text,
    created_by text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT dispatch_reception_pkey PRIMARY KEY (id_reception),
    CONSTRAINT dispatch_reception_dispatch_id_fkey FOREIGN KEY (dispatch_id)
        REFERENCES public.dispatch (id_dispatch) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dispatch_reception
    OWNER to nextgen;


CREATE SEQUENCE public.dispatch_reception_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.dispatch_reception_id_seq
    OWNED BY public.dispatch_reception.id_reception;

ALTER SEQUENCE public.dispatch_reception_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.dispatch_reception
    ALTER COLUMN id_reception SET DEFAULT nextval('dispatch_reception_id_seq'::regclass);


------------------------------------------------------------------------------------------------------------------


CREATE TABLE public.dispatch_reception_detail
(
    id_reception_detail integer NOT NULL,
    reception_id integer,
    product_id integer,
    expected_quantity integer,
    received_quantity integer,
    observations text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT reception_detail_pkey PRIMARY KEY (id_reception_detail),
    CONSTRAINT reception_detail_fkey FOREIGN KEY (reception_id)
        REFERENCES public.dispatch_reception (id_reception) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT reception_detail_product_fkey FOREIGN KEY (product_id)
        REFERENCES public.dispatch_products(id_product) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dispatch_reception_detail
    OWNER to nextgen;


CREATE SEQUENCE public.dispatch_reception_detail_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.dispatch_reception_detail_id_seq
    OWNED BY public.dispatch_reception_detail.id_reception_detail;

ALTER SEQUENCE public.dispatch_reception_detail_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.dispatch_reception_detail
    ALTER COLUMN id_reception_detail SET DEFAULT nextval('dispatch_reception_detail_id_seq'::regclass);


-------------------------------------------------------------------------------------------------------

CREATE TABLE public.biomar_entry_report
(
    id_entry_report integer NOT NULL,
    dni text,
    names_visit text,
    status text DEFAULT 'Pendiente Salida';
    reason_visit text,
    area_visit_id integer,
    person_charge_id integer,
    material_entry integer,
    observations text,
    created_by text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT entry_report_pkey PRIMARY KEY (id_entry_report)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.biomar_entry_report
    OWNER to nextgen;


CREATE SEQUENCE public.biomar_entry_report_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE public.biomar_entry_report_id_seq
    OWNED BY public.biomar_entry_report.id_entry_report;

ALTER SEQUENCE public.biomar_entry_report_id_seq
    OWNER TO nextgen;

ALTER TABLE IF EXISTS public.biomar_entry_report
    ALTER COLUMN id_entry_report SET DEFAULT nextval('biomar_entry_report_id_seq'::regclass);