-- =====================================================================
-- Controle de investimentos: esquema do banco (PostgreSQL)
-- Roda do zero em um banco vazio:  psql -d investimentos -f schema.sql
-- Para recomeçar:                   drop schema investimentos cascade;
-- =====================================================================

create schema if not exists investimentos;

-- =======================================
-- ------ Tabelas de apoio ---------------

create table investimentos.classe_ativo (
	id_classe_ativo smallint generated always as identity primary key
	, classe_ativo text not null
);

insert into investimentos.classe_ativo (classe_ativo)
values ('Ação'), ('Fundo Imobiliário'), ('Renda Fixa');

--------------------------------------------------

create table investimentos.ativos (
	id_ativos int generated always as identity primary key
	, ticker text not null unique
	, nome text
	, id_classe_ativo smallint not null references investimentos.classe_ativo (id_classe_ativo)
);

--------------------------------------------------

create table investimentos.tipo_proventos (
	id_tipo_provento int generated always as identity primary key
	, tipo_provento text not null
);

insert into investimentos.tipo_proventos (tipo_provento)
values ('DIVIDENDO'), ('JCP'), ('RENDIMENTO'), ('OUTROS');

---------------------------------------------------

create table investimentos.instituicao_financeira (
	id_inst_financeira smallint generated always as identity primary key,
	nome text not null,
	cnpj text null,
	criado_em date default current_date not null,
	constraint corretora_cnpj_key unique (cnpj)
);

insert into investimentos.instituicao_financeira (nome, cnpj)
values ('BB Banco de Investimento', '24.933.830/0001-30');

---------------------------------------------------

create table investimentos.tipo_operacao (
	id_tipo_operacao smallint generated always as identity primary key
	, tipo_operacao text not null unique
);

insert into investimentos.tipo_operacao (tipo_operacao)
values ('COMPRA'), ('VENDA'), ('BONIFICAÇÃO');

-- ========================================

-- ------ Tabelas Fato --------------------

create table investimentos.nota_corretagem (
	id_nota_corretagem int generated always as identity primary key,
	id_inst_financeira smallint not null references investimentos.instituicao_financeira (id_inst_financeira),
	numero_nota text not null,
	data_pregao date not null,
	data_liquidacao date null,
	valor_operacoes numeric(10, 2) default 0 not null,
	valor_taxas numeric(10, 2) default 0 not null,
	url_pdf text null,
	constraint nota_corretagem_inst_financeira_data_nota_key
		unique (id_inst_financeira, numero_nota, data_pregao)
);

create table investimentos.operacoes (
	id_operacao int generated always as identity primary key,
	id_nota_corretagem int null references investimentos.nota_corretagem (id_nota_corretagem),
	id_ativos int not null references investimentos.ativos (id_ativos),
	tipo_operacao text not null references investimentos.tipo_operacao (tipo_operacao),
	data_operacao date not null,
	quantidade int not null check (quantidade > 0),
	preco_unitario numeric(10, 2) not null check (preco_unitario >= 0),
	taxa_rateada numeric(10, 2) not null check (taxa_rateada >= 0),
	criado_em date default current_date not null
);

create table investimentos.proventos (
	id_provento int generated always as identity primary key,
	id_tipo_provento int not null references investimentos.tipo_proventos (id_tipo_provento),
	id_ativos int not null references investimentos.ativos (id_ativos),
	data_pagamento date not null,
	valor_liquido numeric(10, 2) not null
);

create table investimentos.cotacoes (
	id_ativos int not null references investimentos.ativos (id_ativos),
	data_cotacao date not null,
	preco_fechamento numeric(10, 2) not null check (preco_fechamento >= 0),
	primary key (id_ativos, data_cotacao)
);

create table investimentos.aportes (
	id_aporte int generated always as identity primary key,
	id_inst_financeira smallint references investimentos.instituicao_financeira (id_inst_financeira),
	data_aporte date not null,
	valor_aporte numeric(10, 2) not null check (valor_aporte <> 0)
);
