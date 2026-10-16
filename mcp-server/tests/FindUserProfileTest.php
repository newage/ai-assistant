<?php

declare(strict_types=1);

namespace Mcp\Tests;

final class FindUserProfileTest extends McpTestCase
{
    public function testLookupById(): void
    {
        $result = $this->callTool('find_user_profile', ['user_id' => 1]);

        $this->assertFalse($result['isError']);
        $user = $this->payload($result);
        $this->assertSame(1, (int) $user['id']);
        $this->assertSame('olena1@example.com', $user['email']);
        $this->assertSame(['id', 'email', 'name', 'created_at'], array_keys($user));
    }

    public function testLookupByEmail(): void
    {
        $result = $this->callTool('find_user_profile', ['email' => 'andrii2@example.com']);

        $this->assertFalse($result['isError']);
        $this->assertSame(2, (int) $this->payload($result)['id']);
    }

    public function testUnknownIdIsNotFound(): void
    {
        $result = $this->callTool('find_user_profile', ['user_id' => 99999]);

        $this->assertTrue($result['isError']);
        $this->assertSame('User not found.', $result['content'][0]['text']);
    }

    public function testUnknownEmailIsNotFound(): void
    {
        $result = $this->callTool('find_user_profile', ['email' => 'nobody@example.com']);

        $this->assertTrue($result['isError']);
        $this->assertSame('User not found.', $result['content'][0]['text']);
    }

    public function testNoIdentifierIsValidationError(): void
    {
        $result = $this->callTool('find_user_profile', []);

        $this->assertTrue($result['isError']);
        $this->assertStringContainsString('Validation error', $result['content'][0]['text']);
    }

    public function testSqlInjectionAttemptIsHarmless(): void
    {
        $result = $this->callTool('find_user_profile', ['email' => "' OR '1'='1"]);

        $this->assertTrue($result['isError']);
        $this->assertSame('User not found.', $result['content'][0]['text']);
    }
}
