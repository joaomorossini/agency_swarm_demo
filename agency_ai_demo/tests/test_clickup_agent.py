import os
import sys
import traceback
from dotenv import load_dotenv
from openai import AzureOpenAI
from agency_swarm import set_openai_client, Agent, Agency

from tools.clickup_tools import initialize_clickup_tools

load_dotenv()


def main():
    try:
        # Accept query from command line arguments if provided
        if len(sys.argv) > 1:
            query = sys.argv[1]
        else:
            # Default query if no argument provided
            query = 'Use the create_task_tool to create a new task in list_id 901307715461 with name "API TEST TASK" and assignees [81918955]. Make sure to pass the list_id parameter correctly.'

        print("Initializing OpenAI client...")
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            timeout=10,
            max_retries=5,
        )

        set_openai_client(client)

        print("Converting ClickUp tools...")
        clickup_tools = initialize_clickup_tools()

        # Instructions similar to what's in the notebook
        clickup_instructions = """
        1. GERENCIAMENTO_DE_PROJETOS:
            A equipe usa o ClickUp para gerenciar projetos e tarefas.
            
        1.1 ESTRUTURA_DO_CLICKUP
            -> Workspace: O nível mais alto de organização no ClickUp. Contém todos os seus Espaços.
            --> Space: Uma coleção de Pastas e Listas. É uma maneira de agrupar trabalhos relacionados.
            ---> Folder: Usado para agrupar Listas.
            ----> List: Usado para agrupar tarefas. As listas podem estar em uma Pasta ou diretamente em um Espaço.
            -----> Task: A unidade básica de trabalho no ClickUp, atribuível com datas de vencimento.
            ------> Subtask: Uma tarefa filha de uma Tarefa pai, atribuível a diferentes pessoas.

        1.1.1 IDS_PADRÃO_DO_CLICKUP
            Use esses IDs, a menos que especificado de outra forma
            - 'Workspace' (também conhecido como "team_id"): 12927880
            - ID do espaço 'Projetos': 54804921
            - ID da pasta 'Agentes': 90131663060
            - ID da lista 'test_clickup_tool': 901307715461
            
        1.1.2 USUÁRIOS_ATIVOS_DO_CLICKUP (id, nome de usuário, email)
            - 81918955, João Guilherme Silva Morossini, joaog.morossini@gmail.com
        """

        print("Creating ClickUp agent...")
        clickup_agent = Agent(
            name="clickup_agent",
            description="I am a ClickUp agent that helps manage tasks and projects",
            instructions=clickup_instructions,
            model="gpt-4o",
            tools=clickup_tools,
        )

        # Create the agency with a single agent
        print("Creating agency...")
        agency = Agency(
            agency_chart=[
                clickup_agent,  # Just the clickup agent
            ]
        )

        # Send the query to the agent
        print("Sending query to agent...")
        print(f"Query: '{query}'")
        print("Using agency.get_completion() method...")
        response = agency.get_completion(query)

        print(f"\nAgent response: {response}")

        print("\nDone!")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nTraceback:")
        traceback.print_exception(*sys.exc_info())


if __name__ == "__main__":
    main()
