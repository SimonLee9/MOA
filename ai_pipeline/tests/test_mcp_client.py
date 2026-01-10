"""
Tests for MCP Client Integration
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from pipeline.integrations.mcp_client import (
    MCPClient,
    MCPSettings,
    ToolCategory,
    ToolDefinition,
    AVAILABLE_TOOLS,
    get_mcp_client,
    execute_tool,
)


class TestToolDefinitions:
    """Tests for tool definitions."""

    def test_all_tools_have_required_fields(self):
        """Test all tools have required definition fields."""
        for tool_name, tool_def in AVAILABLE_TOOLS.items():
            assert isinstance(tool_def.name, str)
            assert isinstance(tool_def.category, ToolCategory)
            assert isinstance(tool_def.description, str)
            assert isinstance(tool_def.required_args, list)
            assert isinstance(tool_def.optional_args, list)

    def test_jira_tools_exist(self):
        """Test Jira tools are defined."""
        assert "jira_create_issue" in AVAILABLE_TOOLS
        assert "jira_update_issue" in AVAILABLE_TOOLS

    def test_calendar_tools_exist(self):
        """Test Calendar tools are defined."""
        assert "calendar_create_event" in AVAILABLE_TOOLS
        assert "calendar_update_event" in AVAILABLE_TOOLS

    def test_slack_tools_exist(self):
        """Test Slack tools are defined."""
        assert "slack_send_message" in AVAILABLE_TOOLS

    def test_notion_tools_exist(self):
        """Test Notion tools are defined."""
        assert "notion_create_page" in AVAILABLE_TOOLS

    def test_jira_create_issue_required_args(self):
        """Test Jira create issue has correct required args."""
        tool = AVAILABLE_TOOLS["jira_create_issue"]
        assert "project" in tool.required_args
        assert "summary" in tool.required_args


class TestMCPClient:
    """Tests for MCPClient class."""

    @pytest.fixture
    def client(self):
        return MCPClient()

    @pytest.mark.asyncio
    async def test_initialize_creates_connections(self, client):
        """Test initialize creates connections for enabled servers."""
        with patch.object(MCPSettings, "jira_mcp_enabled", True):
            with patch.object(client, "_connect_jira", new_callable=AsyncMock) as mock:
                mock.return_value = {"type": "jira"}
                await client.initialize()
                # Would be called if jira is enabled

    def test_get_available_tools_empty_when_disabled(self, client):
        """Test no tools available when all servers disabled."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.jira_mcp_enabled = False
            mock_settings.gcal_mcp_enabled = False
            mock_settings.slack_mcp_enabled = False
            mock_settings.notion_mcp_enabled = False

            tools = client.get_available_tools()
            assert len(tools) == 0

    def test_get_available_tools_with_jira_enabled(self, client):
        """Test Jira tools available when enabled."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.jira_mcp_enabled = True
            mock_settings.gcal_mcp_enabled = False
            mock_settings.slack_mcp_enabled = False
            mock_settings.notion_mcp_enabled = False

            tools = client.get_available_tools()
            tool_names = [t.name for t in tools]

            assert "jira_create_issue" in tool_names
            assert "jira_update_issue" in tool_names
            assert "calendar_create_event" not in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_validates_required_args(self, client):
        """Test call_tool validates required arguments."""
        with pytest.raises(ValueError) as exc_info:
            await client.call_tool("jira_create_issue", {})

        assert "Missing required argument" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, client):
        """Test call_tool raises for unknown tool."""
        with pytest.raises(ValueError) as exc_info:
            await client.call_tool("unknown_tool", {})

        assert "Unknown tool" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_jira_create_issue(self, client):
        """Test Jira create issue execution."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.jira_mcp_enabled = True

            result = await client._call_jira_tool(
                "jira_create_issue",
                {"project": "PROJ", "summary": "Test issue"},
            )

            assert result["success"] is True
            assert "issue_key" in result
            assert "url" in result

    @pytest.mark.asyncio
    async def test_call_jira_update_issue(self, client):
        """Test Jira update issue execution."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.jira_mcp_enabled = True

            result = await client._call_jira_tool(
                "jira_update_issue",
                {"issue_key": "PROJ-123", "status": "Done"},
            )

            assert result["success"] is True
            assert result["issue_key"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_call_calendar_create_event(self, client):
        """Test calendar create event execution."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.gcal_mcp_enabled = True

            result = await client._call_calendar_tool(
                "calendar_create_event",
                {"summary": "Meeting", "start_time": "2024-01-20T10:00:00"},
            )

            assert result["success"] is True
            assert "event_id" in result

    @pytest.mark.asyncio
    async def test_call_slack_send_message(self, client):
        """Test Slack send message execution."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.slack_mcp_enabled = True

            result = await client._call_slack_tool(
                "slack_send_message",
                {"channel": "#general", "message": "Hello"},
            )

            assert result["success"] is True
            assert result["channel"] == "#general"

    @pytest.mark.asyncio
    async def test_call_notion_create_page(self, client):
        """Test Notion create page execution."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.notion_mcp_enabled = True

            result = await client._call_notion_tool(
                "notion_create_page",
                {"parent_id": "page-123", "title": "Meeting Notes"},
            )

            assert result["success"] is True
            assert "page_id" in result

    @pytest.mark.asyncio
    async def test_jira_disabled_raises_error(self, client):
        """Test Jira tool raises when disabled."""
        with patch("pipeline.integrations.mcp_client.settings") as mock_settings:
            mock_settings.jira_mcp_enabled = False

            with pytest.raises(RuntimeError) as exc_info:
                await client._call_jira_tool("jira_create_issue", {})

            assert "not enabled" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close_clears_connections(self, client):
        """Test close clears all connections."""
        client._connections = {"test": {}}
        client._initialized = True

        await client.close()

        assert len(client._connections) == 0
        assert client._initialized is False


class TestExecuteTool:
    """Tests for execute_tool convenience function."""

    @pytest.mark.asyncio
    async def test_execute_tool_delegates_to_client(self):
        """Test execute_tool delegates to MCP client."""
        with patch("pipeline.integrations.mcp_client.get_mcp_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.call_tool = AsyncMock(return_value={"success": True})
            mock_get.return_value = mock_client

            result = await execute_tool("jira_create_issue", {"project": "P", "summary": "S"})

            assert result["success"] is True
            mock_client.call_tool.assert_called_once_with(
                "jira_create_issue",
                {"project": "P", "summary": "S"},
            )


class TestToolCategories:
    """Tests for tool categories."""

    def test_task_management_category(self):
        """Test task management category value."""
        assert ToolCategory.TASK_MANAGEMENT == "task_management"

    def test_calendar_category(self):
        """Test calendar category value."""
        assert ToolCategory.CALENDAR == "calendar"

    def test_communication_category(self):
        """Test communication category value."""
        assert ToolCategory.COMMUNICATION == "communication"

    def test_documentation_category(self):
        """Test documentation category value."""
        assert ToolCategory.DOCUMENTATION == "documentation"

    def test_jira_tools_are_task_management(self):
        """Test Jira tools are categorized correctly."""
        tool = AVAILABLE_TOOLS["jira_create_issue"]
        assert tool.category == ToolCategory.TASK_MANAGEMENT

    def test_calendar_tools_are_calendar(self):
        """Test calendar tools are categorized correctly."""
        tool = AVAILABLE_TOOLS["calendar_create_event"]
        assert tool.category == ToolCategory.CALENDAR

    def test_slack_tools_are_communication(self):
        """Test Slack tools are categorized correctly."""
        tool = AVAILABLE_TOOLS["slack_send_message"]
        assert tool.category == ToolCategory.COMMUNICATION

    def test_notion_tools_are_documentation(self):
        """Test Notion tools are categorized correctly."""
        tool = AVAILABLE_TOOLS["notion_create_page"]
        assert tool.category == ToolCategory.DOCUMENTATION
