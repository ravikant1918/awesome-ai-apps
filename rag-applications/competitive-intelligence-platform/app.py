import streamlit as st
import os
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import random
import numpy as np

# LangChain and LLM imports
from langchain_community.llms import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_anthropic import Anthropic

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Competitive Intelligence Platform",
    page_icon="🎯",
    layout="wide"
)

class ConfigurationManager:
    """Manage API keys and model configurations"""
    
    def __init__(self):
        self.config_file = "config_storage.json"
        self.load_configurations()
    
    def load_configurations(self):
        """Load saved configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    configs = json.load(f)
                    # Store in session state
                    if 'saved_configs' not in st.session_state:
                        st.session_state.saved_configs = configs
            else:
                if 'saved_configs' not in st.session_state:
                    st.session_state.saved_configs = {}
        except Exception as e:
            st.error(f"Error loading configurations: {str(e)}")
            if 'saved_configs' not in st.session_state:
                st.session_state.saved_configs = {}
    
    def save_configuration(self, provider, model_name, api_key, config_name):
        """Save a new configuration"""
        try:
            if 'saved_configs' not in st.session_state:
                st.session_state.saved_configs = {}
            
            config_key = f"{provider}_{config_name}"
            st.session_state.saved_configs[config_key] = {
                'provider': provider,
                'model_name': model_name,
                'api_key': api_key,
                'config_name': config_name,
                'created_at': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(st.session_state.saved_configs, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get_saved_configs(self):
        """Get all saved configurations"""
        return st.session_state.get('saved_configs', {})
    
    def get_config(self, config_key):
        """Get a specific configuration"""
        return st.session_state.saved_configs.get(config_key)
    
    def delete_config(self, config_key):
        """Delete a saved configuration"""
        try:
            if config_key in st.session_state.saved_configs:
                del st.session_state.saved_configs[config_key]
                
                # Save to file
                with open(self.config_file, 'w') as f:
                    json.dump(st.session_state.saved_configs, f, indent=2)
                
                return True
        except Exception as e:
            st.error(f"Error deleting configuration: {str(e)}")
            return False
    
    def get_providers_with_saved_keys(self):
        """Get list of providers that have saved API keys"""
        providers = set()
        for config in st.session_state.saved_configs.values():
            providers.add(config['provider'])
        return list(providers)

class CompetitiveIntelligencePlatform:
    def __init__(self):
        # LLM and embedding components
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.qa_chain = None
        self.current_provider = None
        self.current_model = None
        
        # Data storage
        self.competitor_analyses = []
        self.market_reports = []
        self.intelligence_alerts = []
        self.intelligence_stats = {}
        
        # Vectorstore path
        self.vectorstore_path = "./competitive_intelligence_db"
    
    def get_available_providers(self):
        """Get list of available LLM providers"""
        return {
            'OpenAI': {
                'models': ['gpt-3.5-turbo-instruct', 'gpt-4-turbo-preview', 'gpt-4'],
                'requires_key': True,
                'embedding_model': 'text-embedding-ada-002'
            },
            'Google Gemini': {
                'models': ['gemini-pro', 'gemini-1.5-pro'],
                'requires_key': True,
                'embedding_model': 'models/embedding-001'
            },
            'Anthropic': {
                'models': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
                'requires_key': True,
                'embedding_model': 'huggingface'
            }
        }
    
    def initialize_system(self, provider, model_name, api_key, temperature=0.1):
        """Initialize the system with selected provider and model"""
        try:
            if not api_key:
                st.error("Please provide an API key")
                return False
            
            # Initialize LLM based on provider
            if provider == 'OpenAI':
                self.llm = OpenAI(
                    openai_api_key=api_key,
                    temperature=temperature,
                    model_name=model_name
                )
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=api_key,
                    model="text-embedding-ada-002"
                )
            
            elif provider == 'Google Gemini':
                self.llm = GoogleGenerativeAI(
                    google_api_key=api_key,
                    model=model_name,
                    temperature=temperature
                )
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    google_api_key=api_key,
                    model="models/embedding-001"
                )
            
            elif provider == 'Anthropic':
                self.llm = Anthropic(
                    anthropic_api_key=api_key,
                    model_name=model_name,
                    temperature=temperature
                )
                # For Anthropic, use HuggingFace embeddings or OpenAI if available
                openai_key = st.session_state.get('openai_api_key_for_embeddings', '')
                if openai_key:
                    self.embeddings = OpenAIEmbeddings(
                        openai_api_key=openai_key,
                        model="text-embedding-ada-002"
                    )
                else:
                    self.embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-mpnet-base-v2"
                    )
            
            # Initialize vector store
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.vectorstore_path
            )
            
            # Initialize QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
                return_source_documents=True
            )
            
            # Initialize sample data
            self.initialize_sample_competitive_data()
            
            # Store current configuration
            self.current_provider = provider
            self.current_model = model_name
            
            return True
            
        except Exception as e:
            st.error(f"Error initializing system: {str(e)}")
            return False
    
    def initialize_sample_competitive_data(self):
        """Initialize sample competitive intelligence data for demonstration"""
        # Check if data already exists
        try:
            existing_data = self.vectorstore.get()
            if existing_data and len(existing_data.get('ids', [])) > 0:
                return  # Data already exists
        except:
            pass
        
        sample_data = [
            {
                'competitor': 'TechCorp Inc.',
                'content': 'Leading technology company with strong market position in cloud services. Revenue: $2.5B, Market share: 15%, Growth rate: 12% YoY. Key strengths: Innovation, brand recognition, customer loyalty.',
                'industry': 'Technology',
                'market_position': 'Leader',
                'threat_level': 'High',
                'revenue': 2500000000,
                'market_share': 15.0
            },
            {
                'competitor': 'InnovateSoft Ltd.',
                'content': 'Emerging software company focusing on AI solutions. Revenue: $800M, Market share: 8%, Growth rate: 25% YoY. Key strengths: Agility, cutting-edge technology, competitive pricing.',
                'industry': 'Software',
                'market_position': 'Challenger',
                'threat_level': 'Medium',
                'revenue': 800000000,
                'market_share': 8.0
            },
            {
                'competitor': 'DataDynamics Corp.',
                'content': 'Data analytics specialist with strong enterprise presence. Revenue: $1.2B, Market share: 10%, Growth rate: 8% YoY. Key strengths: Domain expertise, enterprise relationships, data security.',
                'industry': 'Data Analytics',
                'market_position': 'Specialist',
                'threat_level': 'Medium',
                'revenue': 1200000000,
                'market_share': 10.0
            },
            {
                'competitor': 'CloudFirst Solutions',
                'content': 'Cloud infrastructure provider with global reach. Revenue: $3.1B, Market share: 18%, Growth rate: 15% YoY. Key strengths: Infrastructure scale, global presence, cost efficiency.',
                'industry': 'Cloud Services',
                'market_position': 'Leader',
                'threat_level': 'High',
                'revenue': 3100000000,
                'market_share': 18.0
            },
            {
                'competitor': 'StartupTech Ventures',
                'content': 'Innovative startup with disruptive technology. Revenue: $150M, Market share: 2%, Growth rate: 45% YoY. Key strengths: Innovation, agility, venture backing, emerging technology.',
                'industry': 'Technology',
                'market_position': 'Niche',
                'threat_level': 'Low',
                'revenue': 150000000,
                'market_share': 2.0
            }
        ]
        
        for data in sample_data:
            self.vectorstore.add_texts(
                texts=[data['content']],
                metadatas=[{
                    'competitor': data['competitor'],
                    'industry': data['industry'],
                    'market_position': data['market_position'],
                    'threat_level': data['threat_level'],
                    'revenue': str(data['revenue']),
                    'market_share': str(data['market_share'])
                }]
            )
    
    def analyze_competitor(self, competitor_data, analysis_type):
        """Analyze competitor with intelligent insights"""
        try:
            analysis_prompt = f"""
            Analyze the following competitor data:
            
            Competitor Data: {competitor_data}
            Analysis Type: {analysis_type}
            
            Please provide comprehensive competitive analysis including:
            
            1. COMPETITOR PROFILE ANALYSIS:
               - Company overview and business model assessment
               - Market position and competitive positioning
               - Financial performance and growth trajectory
               - Organizational structure and leadership analysis
            
            2. COMPETITIVE STRENGTHS AND WEAKNESSES:
               - Core competencies and competitive advantages
               - Market strengths and differentiation factors
               - Operational weaknesses and vulnerabilities
               - Strategic gaps and improvement opportunities
            
            3. MARKET STRATEGY EVALUATION:
               - Go-to-market strategy and approach
               - Product and service portfolio analysis
               - Pricing strategy and value proposition
               - Customer acquisition and retention strategies
            
            4. COMPETITIVE THREAT ASSESSMENT:
               - Direct and indirect competitive threats
               - Market disruption potential and innovation capacity
               - Competitive response capabilities and agility
               - Strategic threat level and impact evaluation
            
            5. PERFORMANCE BENCHMARKING:
               - Financial performance comparison and metrics
               - Market share and growth rate analysis
               - Operational efficiency and productivity metrics
               - Customer satisfaction and loyalty indicators
            
            6. STRATEGIC RECOMMENDATIONS:
               - Competitive response strategies and tactics
               - Defensive and offensive strategic options
               - Market positioning and differentiation opportunities
               - Competitive monitoring and intelligence priorities
            
            Provide actionable competitive intelligence insights and strategic recommendations.
            """
            
            competitor_analysis = self.llm(analysis_prompt)
            
            analysis_entry = {
                'id': len(self.competitor_analyses) + 1,
                'timestamp': datetime.now().isoformat(),
                'competitor_data': competitor_data,
                'analysis_type': analysis_type,
                'analysis': competitor_analysis,
                'threat_score': random.uniform(60, 95),
                'competitive_strength': random.uniform(70, 90),
                'market_impact': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'provider': self.current_provider,
                'model': self.current_model
            }
            
            self.competitor_analyses.append(analysis_entry)
            
            return analysis_entry
            
        except Exception as e:
            return f"Error analyzing competitor: {str(e)}"
    
    def generate_market_intelligence_report(self, market_context, report_scope):
        """Generate comprehensive market intelligence report"""
        try:
            report_prompt = f"""
            Generate market intelligence report for: {market_context}
            Report Scope: {report_scope}
            
            Please provide comprehensive market intelligence including:
            
            1. MARKET LANDSCAPE OVERVIEW:
               - Market size, growth, and dynamics analysis
               - Key market segments and customer demographics
               - Market trends and driving factors
               - Regulatory environment and compliance requirements
            
            2. COMPETITIVE LANDSCAPE ANALYSIS:
               - Major competitors and market leaders identification
               - Competitive positioning and market share analysis
               - Competitive strategies and differentiation approaches
               - New entrants and emerging competitive threats
            
            3. MARKET OPPORTUNITIES AND THREATS:
               - Growth opportunities and market gaps identification
               - Emerging market trends and technology disruptions
               - Competitive threats and market challenges
               - Strategic opportunities for market entry and expansion
            
            4. CUSTOMER AND DEMAND ANALYSIS:
               - Customer needs and preferences assessment
               - Demand patterns and purchasing behavior analysis
               - Customer satisfaction and loyalty evaluation
               - Market demand forecasting and projections
            
            5. TECHNOLOGY AND INNOVATION TRENDS:
               - Technology trends and innovation developments
               - Disruptive technologies and market impact
               - Innovation strategies and R&D investments
               - Technology adoption and market readiness
            
            6. STRATEGIC MARKET INSIGHTS:
               - Market entry and expansion strategies
               - Competitive positioning and differentiation recommendations
               - Partnership and alliance opportunities
               - Market timing and strategic priorities
            
            Provide actionable market intelligence with strategic insights and recommendations.
            """
            
            market_report = self.llm(report_prompt)
            
            report_entry = {
                'id': len(self.market_reports) + 1,
                'timestamp': datetime.now().isoformat(),
                'market_context': market_context,
                'report_scope': report_scope,
                'report': market_report,
                'market_attractiveness': random.uniform(70, 95),
                'competitive_intensity': random.uniform(60, 90),
                'provider': self.current_provider,
                'model': self.current_model
            }
            
            self.market_reports.append(report_entry)
            
            return market_report
            
        except Exception as e:
            return f"Error generating market intelligence report: {str(e)}"
    
    def create_competitive_dashboard(self):
        """Create comprehensive competitive intelligence dashboard"""
        metrics = {
            'Competitors Monitored': [25, 28, 26, 32, 30, 35],
            'Threat Level (Avg)': [6.8, 7.2, 6.9, 7.5, 7.1, 7.8],
            'Market Share Tracked (%)': [85, 88, 86, 91, 89, 94],
            'Intelligence Alerts': [45, 52, 48, 58, 55, 62],
            'Analysis Accuracy (%)': [88, 91, 89, 94, 92, 96],
            'Strategic Value Score': [8.2, 8.5, 8.3, 8.8, 8.6, 9.1]
        }
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=list(metrics.keys()),
            specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
        )
        
        positions = [(1,1), (1,2), (1,3), (2,1), (2,2), (2,3)]
        
        for i, (metric, values) in enumerate(metrics.items()):
            row, col = positions[i]
            
            fig.add_trace(
                go.Scatter(x=months, y=values, mode='lines+markers', name=metric, showlegend=False),
                row=row, col=col
            )
        
        fig.update_layout(
            title="Competitive Intelligence Platform Performance Dashboard",
            height=600
        )
        
        return fig
    
    def create_threat_level_chart(self):
        """Create competitive threat level distribution chart"""
        threat_levels = ['Low', 'Medium', 'High', 'Critical']
        competitor_counts = [8, 15, 10, 2]
        colors = ['green', 'yellow', 'orange', 'red']
        
        fig = go.Figure(data=[
            go.Bar(x=threat_levels, y=competitor_counts, marker_color=colors)
        ])
        
        fig.update_layout(
            title='Competitive Threat Level Distribution',
            xaxis_title='Threat Level',
            yaxis_title='Number of Competitors',
            height=400
        )
        
        return fig
    
    def create_market_share_chart(self):
        """Create market share analysis visualization"""
        companies = ['Our Company', 'TechCorp Inc.', 'CloudFirst Solutions', 'DataDynamics Corp.', 'InnovateSoft Ltd.', 'Others']
        market_shares = [20, 18, 15, 10, 8, 29]
        colors = ['blue', 'lightcoral', 'lightgreen', 'gold', 'plum', 'lightgray']
        
        fig = px.pie(
            values=market_shares,
            names=companies,
            title='Market Share Distribution (%)',
            color_discrete_sequence=colors
        )
        
        fig.update_layout(height=400)
        return fig
    
    def export_intelligence_report(self):
        """Export competitive intelligence report as downloadable file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"competitive_intelligence_report_{timestamp}.json"
        
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "system_config": {
                "provider": self.current_provider,
                "model": self.current_model
            },
            "competitor_analyses": self.competitor_analyses,
            "market_reports": self.market_reports,
            "intelligence_alerts": self.intelligence_alerts,
            "intelligence_stats": self.intelligence_stats,
            "summary": {
                "total_analyses": len(self.competitor_analyses),
                "total_reports": len(self.market_reports),
                "avg_threat_score": sum(a.get('threat_score', 0) for a in self.competitor_analyses) / len(self.competitor_analyses) if self.competitor_analyses else 0,
                "avg_competitive_strength": sum(a.get('competitive_strength', 0) for a in self.competitor_analyses) / len(self.competitor_analyses) if self.competitor_analyses else 0,
                "avg_market_attractiveness": sum(r.get('market_attractiveness', 0) for r in self.market_reports) / len(self.market_reports) if self.market_reports else 0
            }
        }
        
        return filename, json.dumps(export_data, indent=2)

def main():
    st.title("🎯 Competitive Intelligence Platform")
    st.caption("AI-powered competitive analysis and market intelligence")
    
    # Initialize session state
    if "competitive_intelligence" not in st.session_state:
        st.session_state.competitive_intelligence = CompetitiveIntelligencePlatform()
    
    if "system_initialized" not in st.session_state:
        st.session_state.system_initialized = False
    
    if "config_manager" not in st.session_state:
        st.session_state.config_manager = ConfigurationManager()
    
    intelligence_system = st.session_state.competitive_intelligence
    config_manager = st.session_state.config_manager
    
    with st.sidebar:        
        st.markdown("### 🎯 Intelligence Mode")
        
        mode = st.selectbox(
            "Choose Service",
            ["Competitor Analysis", "Market Intelligence", "Intelligence Dashboard"],
            help="Select the type of competitive intelligence service"
        )
        st.divider()
        if st.session_state.system_initialized and intelligence_system.llm:
            st.success(f"✅ Active LLM: {intelligence_system.current_provider} - {intelligence_system.current_model}")
        
        with st.expander("⚙️ System Configuration", expanded=False):
            st.markdown("### LLM Configuration")
            # Configuration mode selection
            config_mode = st.radio(
                "Configuration Mode",
                ["Use Saved Configuration", "New Configuration"],
                help="Choose to use saved configuration or create new one"
            )
            
            if config_mode == "Use Saved Configuration":
                saved_configs = config_manager.get_saved_configs()
                
                if saved_configs:
                    config_options = [f"{v['config_name']} ({v['provider']} - {v['model_name']})" 
                                    for k, v in saved_configs.items()]
                    config_keys = list(saved_configs.keys())
                    
                    selected_config_display = st.selectbox(
                        "Select Saved Configuration",
                        options=config_options,
                        help="Choose a saved configuration"
                    )
                    
                    selected_config_key = config_keys[config_options.index(selected_config_display)]
                    selected_config = config_manager.get_config(selected_config_key)
                    
                    if selected_config:
                        st.info(f"**Provider:** {selected_config['provider']}\n\n**Model:** {selected_config['model_name']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🚀 Auto Initialize", type="primary"):
                                with st.spinner(f"Initializing {selected_config['provider']} {selected_config['model_name']}..."):
                                    if intelligence_system.initialize_system(
                                        selected_config['provider'],
                                        selected_config['model_name'],
                                        selected_config['api_key'],
                                        0.1
                                    ):
                                        st.session_state.system_initialized = True
                                        st.success(f"✅ System initialized!")
                                        st.rerun()
                        
                        with col2:
                            if st.button("🗑️ Delete", type="secondary"):
                                if config_manager.delete_config(selected_config_key):
                                    st.success("Configuration deleted!")
                                    st.rerun()
                else:
                    st.warning("No saved configurations found. Please create a new configuration.")
            
            else:  # New Configuration
                st.markdown("### Add New Configuration")
                
                # Provider selection
                providers = intelligence_system.get_available_providers()
                selected_provider = st.selectbox(
                    "Select AI Provider",
                    options=list(providers.keys()),
                    help="Choose your AI provider"
                )
                
                # Model selection based on provider
    
                available_models = providers[selected_provider]['models']
                # selected_model = st.selectbox(
                #     "Select Model",
                #     options=available_models,
                #     help="Choose the specific model to use"
                # )
                # Modal name key input
                selected_model = st.text_input(
                    "Model Name Key",
                    placeholder="e.g., gpt-4, gemini-pro, claude-3-opus-20240229",
                    help="Enter the exact model name as per provider documentation"
                )
                
                # API Key input
                api_key = st.text_input(
                    f"{selected_provider} API Key",
                    type="password",
                    help=f"Enter your {selected_provider} API key",
                    key=f"new_api_key_{selected_provider}"
                )
                
                # Configuration name
                config_name = st.text_input(
                    "Configuration Name",
                    placeholder="e.g., Production, Development, Testing",
                    help="Give this configuration a memorable name"
                )
                
                # Additional embedding key for Anthropic
                if selected_provider == 'Anthropic':
                    with st.expander("⚙️ Embedding Configuration (Optional)"):
                        st.info("Anthropic models require embeddings. You can provide an OpenAI key for better embeddings, or we'll use free HuggingFace embeddings.")
                        openai_embedding_key = st.text_input(
                            "OpenAI API Key (for embeddings)",
                            type="password",
                            help="Optional: Provide OpenAI key for better embeddings"
                        )
                        if openai_embedding_key:
                            st.session_state.openai_api_key_for_embeddings = openai_embedding_key
                
                # Temperature slider
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.1,
                    step=0.1,
                    help="Higher values make output more creative but less focused"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Save and Initialize button
                    if st.button("💾 Save & Initialize", type="primary", disabled=not (api_key and config_name)):
                        if config_manager.save_configuration(selected_provider, selected_model, api_key, config_name):
                            with st.spinner(f"Initializing {selected_provider} {selected_model}..."):
                                if intelligence_system.initialize_system(selected_provider, selected_model, api_key, temperature):
                                    st.session_state.system_initialized = True
                                    st.success(f"✅ Configuration saved and system initialized!")
                                    st.rerun()
                                else:
                                    st.error("Failed to initialize system. Check your API key and configuration.")
                        else:
                            st.error("Failed to save configuration.")
                
                with col2:
                    # Just Initialize button (without saving)
                    if st.button("🚀 Initialize Only", disabled=not api_key):
                        with st.spinner(f"Initializing {selected_provider} {selected_model}..."):
                            if intelligence_system.initialize_system(selected_provider, selected_model, api_key, temperature):
                                st.session_state.system_initialized = True
                                st.success(f"✅ System initialized!")
                                st.rerun()
                            else:
                                st.error("Failed to initialize system. Check your API key and configuration.")
            
            # Show current configuration if initialized

        
        if intelligence_system.competitor_analyses or intelligence_system.market_reports:
            st.markdown("### 📈 System Stats")
            st.metric("Competitor Analyses", len(intelligence_system.competitor_analyses))
            st.metric("Market Reports", len(intelligence_system.market_reports))
            
            if intelligence_system.competitor_analyses:
                avg_threat = sum(a.get('threat_score', 0) for a in intelligence_system.competitor_analyses) / len(intelligence_system.competitor_analyses)
                st.metric("Avg Threat Score", f"{avg_threat:.1f}%")
        
        if intelligence_system.competitor_analyses or intelligence_system.market_reports:
            st.markdown("### 📥 Export Report")
            
            if st.button("Export Intelligence Report"):
                filename, content = intelligence_system.export_intelligence_report()
                if content:
                    st.download_button(
                        "📄 Download Report",
                        content,
                        file_name=filename,
                        mime="application/json"
                    )
        
        # Help section
        with st.expander("ℹ️ Setup Help"):
            st.markdown("""
            ### How to Get API Keys:
            
            **OpenAI:**
            1. Visit [platform.openai.com](https://platform.openai.com/)
            2. Sign up or log in
            3. Go to API Keys section
            4. Create new secret key
            
            **Google Gemini:**
            1. Visit [makersuite.google.com](https://makersuite.google.com/app/apikey)
            2. Sign in with Google account
            3. Create API key
            
            **Anthropic:**
            1. Visit [console.anthropic.com](https://console.anthropic.com/)
            2. Sign up or log in
            3. Go to API Keys
            4. Generate new key
            """)
    
    # Main content area
    if not st.session_state.system_initialized or not intelligence_system.llm:
        st.warning("⚠️ Please configure and initialize the system using the sidebar.")
        
        st.markdown("""
        ### 🚀 Getting Started
        
        #### Option 1: Use Saved Configuration
        1. Select "Use Saved Configuration" in the sidebar
        2. Choose a saved configuration from the dropdown
        3. Click "Auto Initialize" to start
        
        #### Option 2: Create New Configuration
        1. Select "New Configuration" in the sidebar
        2. Choose your AI provider and model
        3. Enter your API key
        4. Give your configuration a name
        5. Click "Save & Initialize" to save for future use
        6. Or click "Initialize Only" for one-time use
        
        ### 📊 Features
        
        - **Competitor Analysis**: Comprehensive competitor profiling and threat assessment
        - **Market Intelligence**: Market trends and competitive landscape analysis
        - **Strategic Insights**: Strategic positioning and opportunity identification
        - **Performance Benchmarking**: Competitive performance comparison
        - **Intelligence Dashboard**: Visual analytics and KPI tracking
        - **Configuration Management**: Save and reuse API keys and model settings
        """)
        
        return
    
    # Mode-specific content
    if mode == "Competitor Analysis":
        st.header("🎯 Competitor Analysis")
        
        competitor_data = st.text_area(
            "Competitor Data",
            placeholder="Enter competitor information: company details, market position, financial data, strategies...",
            height=200,
            help="Enter competitor data for analysis"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Comprehensive Analysis", "Threat Assessment", "Strategic Analysis", "Financial Analysis", "Market Position Analysis"],
                help="Select the type of competitor analysis"
            )
        
        with col2:
            competitor_category = st.selectbox(
                "Competitor Category",
                ["Direct Competitor", "Indirect Competitor", "Potential Entrant", "Substitute Provider", "All Categories"],
                help="Choose the competitor category"
            )
        
        if st.button("🎯 Analyze Competitor", type="primary", disabled=not competitor_data):
            with st.spinner("Analyzing competitor data..."):
                result = intelligence_system.analyze_competitor(competitor_data, analysis_type)
                
                if isinstance(result, dict):
                    st.success("✅ Competitor analysis complete!")
                    
                    st.markdown("### 💡 Competitor Analysis")
                    st.markdown(result['analysis'])
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Threat Score", f"{result['threat_score']:.1f}%")
                    
                    with col2:
                        st.metric("Competitive Strength", f"{result['competitive_strength']:.1f}%")
                    
                    with col3:
                        st.metric("Market Impact", result['market_impact'])
                    
                    st.info(f"Analysis generated using: {result['provider']} - {result['model']}")
                else:
                    st.error(result)
    
    elif mode == "Market Intelligence":
        st.header("📊 Market Intelligence Report")
        
        market_context = st.text_area(
            "Market Context",
            placeholder="Describe market intelligence requirements: industry, market segment, geographic scope, analysis objectives...",
            height=150,
            help="Provide context for market intelligence analysis"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_scope = st.selectbox(
                "Report Scope",
                ["Market Overview", "Competitive Landscape", "Market Opportunities", "Threat Analysis", "Comprehensive Report"],
                help="Select the market intelligence report scope"
            )
        
        with col2:
            time_horizon = st.selectbox(
                "Time Horizon",
                ["Current State", "6 Month Outlook", "1 Year Forecast", "3 Year Strategic"],
                help="Choose the analysis time horizon"
            )
        
        if st.button("📊 Generate Intelligence Report", type="primary", disabled=not market_context):
            with st.spinner("Generating comprehensive market intelligence report..."):
                context = f"{market_context} | Time Horizon: {time_horizon}"
                report = intelligence_system.generate_market_intelligence_report(context, report_scope)
                
                st.success("✅ Market intelligence report generated!")
                
                st.markdown("### 📊 Market Intelligence Report")
                st.markdown(report)
                
                if intelligence_system.market_reports:
                    latest_report = intelligence_system.market_reports[-1]
                    st.info(f"Report generated using: {latest_report['provider']} - {latest_report['model']}")
    
    elif mode == "Intelligence Dashboard":
        st.header("📊 Intelligence Dashboard")
        
        dashboard_chart = intelligence_system.create_competitive_dashboard()
        if dashboard_chart:
            st.plotly_chart(dashboard_chart, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            threat_chart = intelligence_system.create_threat_level_chart()
            if threat_chart:
                st.plotly_chart(threat_chart, use_container_width=True)
        
        with col2:
            market_share_chart = intelligence_system.create_market_share_chart()
            if market_share_chart:
                st.plotly_chart(market_share_chart, use_container_width=True)
        
        st.markdown("### 📈 Intelligence KPIs")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Competitors Monitored", "35", "5")
        
        with col2:
            st.metric("Threat Level", "7.8/10", "0.7")
        
        with col3:
            st.metric("Market Coverage", "94%", "5%")
        
        with col4:
            st.metric("Strategic Value", "9.1/10", "0.5")
    
    # Intelligence History
    if intelligence_system.competitor_analyses or intelligence_system.market_reports:
        st.header("📚 Intelligence History")
        
        if intelligence_system.competitor_analyses:
            with st.expander("🎯 Recent Competitor Analyses"):
                for analysis in reversed(intelligence_system.competitor_analyses[-5:]):
                    st.markdown(f"**Analysis {analysis['id']}** ({analysis['provider']} - {analysis['model']})")
                    st.markdown(f"Type: {analysis['analysis_type']} | Threat: {analysis['threat_score']:.1f}% | Impact: {analysis['market_impact']}")
                    st.markdown(f"Data: {analysis['competitor_data'][:100]}...")
                    st.divider()
        
        if intelligence_system.market_reports:
            with st.expander("📊 Recent Market Reports"):
                for report in reversed(intelligence_system.market_reports[-5:]):
                    st.markdown(f"**Report {report['id']}** ({report['provider']} - {report['model']})")
                    st.markdown(f"Scope: {report['report_scope']} | Attractiveness: {report['market_attractiveness']:.1f}% | Intensity: {report['competitive_intensity']:.1f}%")
                    st.markdown(f"Context: {report['market_context'][:100]}...")
                    st.divider()

if __name__ == "__main__":
    main()
 

# Additional utility functions for enhanced functionality

def create_env_template():
    """Create a template .env file for users"""
    template = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODELS=gpt-3.5-turbo-instruct,gpt-4-turbo-preview,gpt-4

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MODELS=gemini-pro,gemini-1.5-pro

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODELS=claude-3-opus-20240229,claude-3-sonnet-20240229,claude-3-haiku-20240307

# Model Settings
MODEL_TEMPERATURES=0.1,0.3,0.7

# Vector Store Configuration
VECTORSTORE_PATH=./competitive_intelligence_db
"""
    return template

