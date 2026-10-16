<?php

declare(strict_types=1);

namespace Mcp\Tests;

final class GetUserActivityTest extends McpTestCase
{
    public function testUserWithActivity(): void
    {
        $result = $this->callTool('get_user_activity', ['user_id' => 1]);

        $this->assertFalse($result['isError']);
        $data = $this->payload($result);
        $this->assertSame(1, $data['user_id']);
        $this->assertNotEmpty($data['activity']);
        $this->assertSame(['id', 'action', 'created_at'], array_keys($data['activity'][0]));
    }

    public function testUnknownUser(): void
    {
        $result = $this->callTool('get_user_activity', ['user_id' => 99999]);

        $this->assertTrue($result['isError']);
        $this->assertSame('User not found.', $result['content'][0]['text']);
    }

    public function testMissingUserId(): void
    {
        $result = $this->callTool('get_user_activity', []);

        $this->assertTrue($result['isError']);
        $this->assertStringContainsString('Validation error', $result['content'][0]['text']);
    }
}
