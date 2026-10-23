--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4 (Debian 15.4-2.pgdg120+1)
-- Dumped by pg_dump version 15.4 (Debian 15.4-2.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chunks (
    id integer NOT NULL,
    paper_id integer NOT NULL,
    pmid character varying(20) NOT NULL,
    chunk_index integer NOT NULL,
    char_start integer,
    char_end integer,
    chunk_text text NOT NULL,
    embedding public.vector(1024),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chunks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chunks_id_seq OWNED BY public.chunks.id;


--
-- Name: evaluation_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluation_evidence (
    id integer NOT NULL,
    evaluation_id integer NOT NULL,
    kcc_id character varying(10) NOT NULL,
    kcc_title character varying(100) NOT NULL,
    paper_id integer NOT NULL,
    pmid character varying(20) NOT NULL,
    model_category character varying(50) NOT NULL,
    base_score integer NOT NULL,
    quartile character varying(15) NOT NULL,
    best_query_code character varying(20) NOT NULL,
    max_cosine_score double precision NOT NULL,
    max_rerank_score double precision NOT NULL,
    matched_chunks jsonb NOT NULL,
    is_selected boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: evaluation_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluation_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evaluation_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluation_evidence_id_seq OWNED BY public.evaluation_evidence.id;


--
-- Name: evaluations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluations (
    id integer NOT NULL,
    cas_number character varying(50) NOT NULL,
    chemical_name character varying(255) NOT NULL,
    filter_criteria jsonb,
    status character varying(30) NOT NULL,
    hazard_score integer,
    risk_level character varying(50),
    kcc_scores jsonb,
    expert_report text,
    public_report text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: evaluations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evaluations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evaluations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evaluations_id_seq OWNED BY public.evaluations.id;


--
-- Name: journal_rankings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.journal_rankings (
    id integer NOT NULL,
    issn character varying(20) NOT NULL,
    journal_title text NOT NULL,
    quartile character varying(10) NOT NULL,
    sjr_score double precision,
    h_index integer,
    ranking_year integer
);


--
-- Name: journal_rankings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.journal_rankings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: journal_rankings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.journal_rankings_id_seq OWNED BY public.journal_rankings.id;


--
-- Name: kcc_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kcc_queries (
    id integer NOT NULL,
    kcc_id character varying(10) NOT NULL,
    kcc_title character varying(100) NOT NULL,
    query_code character varying(20) NOT NULL,
    query_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: kcc_queries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.kcc_queries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kcc_queries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kcc_queries_id_seq OWNED BY public.kcc_queries.id;


--
-- Name: kcc_query_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kcc_query_embeddings (
    id integer NOT NULL,
    query_id integer NOT NULL,
    query_code character varying(20) NOT NULL,
    embedding public.vector(1024) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: kcc_query_embeddings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.kcc_query_embeddings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kcc_query_embeddings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kcc_query_embeddings_id_seq OWNED BY public.kcc_query_embeddings.id;


--
-- Name: paper_authors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paper_authors (
    id integer NOT NULL,
    paper_id integer NOT NULL,
    pmid character varying(20) NOT NULL,
    author_order integer NOT NULL,
    last_name character varying(100),
    fore_name character varying(100),
    initials character varying(20),
    affiliation text
);


--
-- Name: paper_authors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.paper_authors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: paper_authors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.paper_authors_id_seq OWNED BY public.paper_authors.id;


--
-- Name: paper_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paper_models (
    id integer NOT NULL,
    paper_id integer NOT NULL,
    pmid character varying(20) NOT NULL,
    model_category character varying(50) NOT NULL,
    base_score integer NOT NULL,
    detection_source character varying(50) NOT NULL,
    matched_terms text,
    raw_mesh_terms text
);


--
-- Name: paper_models_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.paper_models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: paper_models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.paper_models_id_seq OWNED BY public.paper_models.id;


--
-- Name: papers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.papers (
    id integer NOT NULL,
    cas_number character varying(50) NOT NULL,
    pmid character varying(20) NOT NULL,
    doi character varying(100),
    pmcid character varying(30),
    article_title text NOT NULL,
    journal_title text,
    iso_abbreviation character varying(255),
    abstract text NOT NULL,
    pub_date character varying(50),
    pub_year integer,
    pub_type text,
    issn character varying(20),
    issn_linking character varying(20),
    citation_count integer,
    quartile character varying(15),
    created_at timestamp with time zone DEFAULT now(),
    is_selected boolean DEFAULT false NOT NULL
);


--
-- Name: papers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.papers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: papers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.papers_id_seq OWNED BY public.papers.id;


--
-- Name: target_chemicals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.target_chemicals (
    id integer NOT NULL,
    cas_number character varying(50) NOT NULL,
    chemical_name character varying(255) NOT NULL,
    is_primary boolean,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: target_chemicals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.target_chemicals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: target_chemicals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.target_chemicals_id_seq OWNED BY public.target_chemicals.id;


--
-- Name: chunks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks ALTER COLUMN id SET DEFAULT nextval('public.chunks_id_seq'::regclass);


--
-- Name: evaluation_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_evidence ALTER COLUMN id SET DEFAULT nextval('public.evaluation_evidence_id_seq'::regclass);


--
-- Name: evaluations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluations ALTER COLUMN id SET DEFAULT nextval('public.evaluations_id_seq'::regclass);


--
-- Name: journal_rankings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_rankings ALTER COLUMN id SET DEFAULT nextval('public.journal_rankings_id_seq'::regclass);


--
-- Name: kcc_queries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kcc_queries ALTER COLUMN id SET DEFAULT nextval('public.kcc_queries_id_seq'::regclass);


--
-- Name: kcc_query_embeddings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kcc_query_embeddings ALTER COLUMN id SET DEFAULT nextval('public.kcc_query_embeddings_id_seq'::regclass);


--
-- Name: paper_authors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_authors ALTER COLUMN id SET DEFAULT nextval('public.paper_authors_id_seq'::regclass);


--
-- Name: paper_models id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_models ALTER COLUMN id SET DEFAULT nextval('public.paper_models_id_seq'::regclass);


--
-- Name: papers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.papers ALTER COLUMN id SET DEFAULT nextval('public.papers_id_seq'::regclass);


--
-- Name: target_chemicals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_chemicals ALTER COLUMN id SET DEFAULT nextval('public.target_chemicals_id_seq'::regclass);


--
-- Name: chunks chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_pkey PRIMARY KEY (id);


--
-- Name: evaluation_evidence evaluation_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_evidence
    ADD CONSTRAINT evaluation_evidence_pkey PRIMARY KEY (id);


--
-- Name: evaluations evaluations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluations
    ADD CONSTRAINT evaluations_pkey PRIMARY KEY (id);


--
-- Name: journal_rankings journal_rankings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.journal_rankings
    ADD CONSTRAINT journal_rankings_pkey PRIMARY KEY (id);


--
-- Name: kcc_queries kcc_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kcc_queries
    ADD CONSTRAINT kcc_queries_pkey PRIMARY KEY (id);


--
-- Name: kcc_query_embeddings kcc_query_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kcc_query_embeddings
    ADD CONSTRAINT kcc_query_embeddings_pkey PRIMARY KEY (id);


--
-- Name: kcc_query_embeddings kcc_query_embeddings_query_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kcc_query_embeddings
    ADD CONSTRAINT kcc_query_embeddings_query_id_key UNIQUE (query_id);


--
-- Name: paper_authors paper_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_authors
    ADD CONSTRAINT paper_authors_pkey PRIMARY KEY (id);


--
-- Name: paper_models paper_models_paper_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_models
    ADD CONSTRAINT paper_models_paper_id_key UNIQUE (paper_id);


--
-- Name: paper_models paper_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_models
    ADD CONSTRAINT paper_models_pkey PRIMARY KEY (id);


--
-- Name: papers papers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.papers
    ADD CONSTRAINT papers_pkey PRIMARY KEY (id);


--
-- Name: target_chemicals target_chemicals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.target_chemicals
    ADD CONSTRAINT target_chemicals_pkey PRIMARY KEY (id);


--
-- Name: evaluation_evidence uix_eval_kcc_paper; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_evidence
    ADD CONSTRAINT uix_eval_kcc_paper UNIQUE (evaluation_id, kcc_id, paper_id);


--
-- Name: chunks uix_paper_chunk_idx; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT uix_paper_chunk_idx UNIQUE (paper_id, chunk_index);


--
-- Name: idx_chunks_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_embedding_hnsw ON public.chunks USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: ix_chunks_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chunks_id ON public.chunks USING btree (id);


--
-- Name: ix_chunks_paper_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chunks_paper_id ON public.chunks USING btree (paper_id);


--
-- Name: ix_chunks_pmid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chunks_pmid ON public.chunks USING btree (pmid);


--
-- Name: ix_evaluation_evidence_evaluation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_evaluation_id ON public.evaluation_evidence USING btree (evaluation_id);


--
-- Name: ix_evaluation_evidence_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_id ON public.evaluation_evidence USING btree (id);


--
-- Name: ix_evaluation_evidence_is_selected; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_is_selected ON public.evaluation_evidence USING btree (is_selected);


--
-- Name: ix_evaluation_evidence_kcc_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_kcc_id ON public.evaluation_evidence USING btree (kcc_id);


--
-- Name: ix_evaluation_evidence_max_cosine_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_max_cosine_score ON public.evaluation_evidence USING btree (max_cosine_score);


--
-- Name: ix_evaluation_evidence_max_rerank_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_max_rerank_score ON public.evaluation_evidence USING btree (max_rerank_score);


--
-- Name: ix_evaluation_evidence_paper_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_paper_id ON public.evaluation_evidence USING btree (paper_id);


--
-- Name: ix_evaluation_evidence_pmid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluation_evidence_pmid ON public.evaluation_evidence USING btree (pmid);


--
-- Name: ix_evaluations_cas_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluations_cas_number ON public.evaluations USING btree (cas_number);


--
-- Name: ix_evaluations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluations_id ON public.evaluations USING btree (id);


--
-- Name: ix_evaluations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evaluations_status ON public.evaluations USING btree (status);


--
-- Name: ix_journal_rankings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_rankings_id ON public.journal_rankings USING btree (id);


--
-- Name: ix_journal_rankings_issn; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_journal_rankings_issn ON public.journal_rankings USING btree (issn);


--
-- Name: ix_journal_rankings_quartile; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_journal_rankings_quartile ON public.journal_rankings USING btree (quartile);


--
-- Name: ix_kcc_queries_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kcc_queries_id ON public.kcc_queries USING btree (id);


--
-- Name: ix_kcc_queries_kcc_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kcc_queries_kcc_id ON public.kcc_queries USING btree (kcc_id);


--
-- Name: ix_kcc_queries_query_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_kcc_queries_query_code ON public.kcc_queries USING btree (query_code);


--
-- Name: ix_kcc_query_embeddings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kcc_query_embeddings_id ON public.kcc_query_embeddings USING btree (id);


--
-- Name: ix_kcc_query_embeddings_query_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_kcc_query_embeddings_query_code ON public.kcc_query_embeddings USING btree (query_code);


--
-- Name: ix_paper_authors_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_authors_id ON public.paper_authors USING btree (id);


--
-- Name: ix_paper_authors_pmid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_authors_pmid ON public.paper_authors USING btree (pmid);


--
-- Name: ix_paper_models_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_models_id ON public.paper_models USING btree (id);


--
-- Name: ix_paper_models_model_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_models_model_category ON public.paper_models USING btree (model_category);


--
-- Name: ix_paper_models_pmid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_models_pmid ON public.paper_models USING btree (pmid);


--
-- Name: ix_papers_cas_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_papers_cas_number ON public.papers USING btree (cas_number);


--
-- Name: ix_papers_citation_count; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_papers_citation_count ON public.papers USING btree (citation_count);


--
-- Name: ix_papers_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_papers_id ON public.papers USING btree (id);


--
-- Name: ix_papers_is_selected; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_papers_is_selected ON public.papers USING btree (is_selected);


--
-- Name: ix_papers_pmid; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_papers_pmid ON public.papers USING btree (pmid);


--
-- Name: ix_papers_pub_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_papers_pub_year ON public.papers USING btree (pub_year);


--
-- Name: ix_papers_quartile; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_papers_quartile ON public.papers USING btree (quartile);


--
-- Name: ix_target_chemicals_cas_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_chemicals_cas_number ON public.target_chemicals USING btree (cas_number);


--
-- Name: ix_target_chemicals_chemical_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_target_chemicals_chemical_name ON public.target_chemicals USING btree (chemical_name);


--
-- Name: ix_target_chemicals_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_target_chemicals_id ON public.target_chemicals USING btree (id);


--
-- Name: chunks chunks_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.papers(id) ON DELETE CASCADE;


--
-- Name: evaluation_evidence evaluation_evidence_evaluation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_evidence
    ADD CONSTRAINT evaluation_evidence_evaluation_id_fkey FOREIGN KEY (evaluation_id) REFERENCES public.evaluations(id) ON DELETE CASCADE;


--
-- Name: evaluation_evidence evaluation_evidence_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluation_evidence
    ADD CONSTRAINT evaluation_evidence_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.papers(id) ON DELETE CASCADE;


--
-- Name: kcc_query_embeddings kcc_query_embeddings_query_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kcc_query_embeddings
    ADD CONSTRAINT kcc_query_embeddings_query_id_fkey FOREIGN KEY (query_id) REFERENCES public.kcc_queries(id) ON DELETE CASCADE;


--
-- Name: paper_authors paper_authors_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_authors
    ADD CONSTRAINT paper_authors_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.papers(id) ON DELETE CASCADE;


--
-- Name: paper_models paper_models_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_models
    ADD CONSTRAINT paper_models_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.papers(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

