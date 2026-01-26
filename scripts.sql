
CREATE TABLE public.category
(
    id_category integer NOT NULL DEFAULT 1,
    name_category text NOT NULL,
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
    id_unity integer NOT NULL DEFAULT nextval('unity_weight_id_seq'::regclass),
    name text NOT NULL,
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