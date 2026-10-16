<?php

declare(strict_types=1);

namespace Mcp\Log;

use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;

/** Builds the per-request logger and applies the request-id and debug rules. */
final class RequestLogger
{
    private const ID_PATTERN = '/\A[A-Za-z0-9._-]{1,64}\z/';
    private const CONTENT_LIMIT = 500;

    public static function requestId(?string $header): string
    {
        return $header !== null && preg_match(self::ID_PATTERN, $header) === 1 ? $header : '-';
    }

    /** Debug when the request asks for it with "true", otherwise only outside production. */
    public static function debugEnabled(?string $header, string $environment): bool
    {
        return $header === 'true' || $environment !== 'prod';
    }

    public static function create(?string $idHeader, ?string $debugHeader, mixed $stream = 'php://stdout'): Logger
    {
        $environment = getenv('ENVIRONMENT') ?: 'local';
        $requestId = self::requestId($idHeader);

        $handler = new StreamHandler($stream, self::debugEnabled($debugHeader, $environment) ? Level::Debug : Level::Info);
        $handler->setFormatter(new JsonFormatter('mcp-server', getenv('LOG_ID') ?: 'dev', $environment, $requestId));

        return new Logger('mcp-server', [$handler], [], new \DateTimeZone('UTC'));
    }

    public static function truncate(mixed $value): string
    {
        $text = is_string($value) ? $value : (json_encode($value, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?: '');

        return mb_strlen($text) <= self::CONTENT_LIMIT ? $text : mb_substr($text, 0, self::CONTENT_LIMIT) . '…';
    }
}
