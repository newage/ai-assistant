<?php

declare(strict_types=1);

namespace Mcp\Log;

use Monolog\Formatter\NormalizerFormatter;
use Monolog\LogRecord;

/** One JSON object per line: priority, service, short_message, x-request-id, extra, timestamp, log_id, environment. */
final class JsonFormatter extends NormalizerFormatter
{
    public function __construct(
        private readonly string $service,
        private readonly string $logId,
        private readonly string $environment,
        private readonly string $requestId,
    ) {
        parent::__construct('Y-m-d\TH:i:s.uP');
    }

    public function format(LogRecord $record): string
    {
        $extra = $this->normalize($record->context + $record->extra);

        return $this->toJson([
            'priority' => strtoupper($record->level->getName()),
            'service' => $this->service,
            'short_message' => $record->message,
            'x-request-id' => $this->requestId,
            'extra' => $extra === [] ? [] : $extra,
            'timestamp' => $record->datetime->setTimezone(new \DateTimeZone('UTC'))->format('Y-m-d\TH:i:s.uP'),
            'log_id' => $this->logId,
            'environment' => $this->environment,
        ]) . "\n";
    }
}
