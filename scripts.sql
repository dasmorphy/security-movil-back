
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
    shipping_guide text,
    description text,
    quantity integer NOT NULL,
    weight integer NOT NULL,
    provider text,
    destiny_intern text,
    authorized_by text,
    observations text,
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
    quantity integer NOT NULL,
    weight integer NOT NULL,
    truck_license text,
    name_driver text,
    person_withdraws text,
    destiny text,
    authorized_by text,
    observations text,
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